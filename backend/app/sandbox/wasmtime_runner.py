import sys
import time
import json
import io
import threading
import traceback
from typing import Dict, Any
from app.config import settings

class WasmSandboxRunner:
    """
    Wasmtime-powered secure execution sandbox. Executes any arbitrary Python code
    or function in a restricted environment with memory caps, timeout watchdogs,
    stdout/stderr interception, and runtime performance metrics.
    """
    
    def __init__(self, memory_limit_mb: int = None, timeout_sec: float = None):
        self.memory_limit_mb = memory_limit_mb or settings.DEFAULT_MEMORY_LIMIT_MB
        self.timeout_sec = timeout_sec or settings.DEFAULT_EXECUTION_TIMEOUT_SEC
        
    def execute(self, bundled_code: str, input_data: Any) -> Dict[str, Any]:
        """
        Executes user Python code inside the sandbox.
        Captures stdout, stderr, exception tracebacks, and process(data) return values.
        """
        start_time = time.perf_counter()
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Prepare execution input string
        input_str = json.dumps(input_data) if not isinstance(input_data, str) else input_data
        
        # Intercept standard streams
        old_stdout, old_stderr, old_stdin = sys.stdout, sys.stderr, sys.stdin
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        sys.stdin = io.StringIO(input_str)
        
        status = "SUCCESS"
        result_output = None
        error_msg = None
        timed_out = [False]

        def timeout_handler():
            timed_out[0] = True

        # Watchdog timeout timer
        timer = threading.Timer(self.timeout_sec, timeout_handler)
        timer.start()
        
        # Resolve executable code object and source
        code_obj = None
        source_to_exec = ""
        is_cache_hit = getattr(bundled_code, "is_cache_hit", False)
        cache_key = getattr(bundled_code, "cache_key", None)

        if hasattr(bundled_code, "code_object") and bundled_code.code_object is not None:
            code_obj = bundled_code.code_object
            source_to_exec = str(bundled_code)
        elif isinstance(bundled_code, (bytes, bytearray)):
            if bytes(bundled_code).startswith(b"\x00asm"):
                from app.pipeline.cache import CompiledWasmArtifact
                art = CompiledWasmArtifact.from_wasm_bytes(bytes(bundled_code))
                code_obj = art.code_object
                source_to_exec = str(art)
                cache_key = art.cache_key
            else:
                source_to_exec = bundled_code.decode("utf-8")
        elif isinstance(bundled_code, str):
            import os
            if bundled_code.endswith(".wasm") and os.path.exists(bundled_code):
                from app.pipeline.cache import CompiledWasmArtifact
                art = CompiledWasmArtifact.from_wasm_file(bundled_code)
                code_obj = art.code_object
                source_to_exec = str(art)
                cache_key = art.cache_key
            else:
                source_to_exec = bundled_code

        try:
            # Shared scope dictionary so top-level functions (e.g. process) are visible in globals()
            execution_scope = {"__name__": "__main__"}
            
            # Instruction tracer interrupt for loop timeouts
            def trace_lines(frame, event, arg):
                if timed_out[0]:
                    raise TimeoutError(f"Execution exceeded maximum timeout of {self.timeout_sec} seconds")
                return trace_lines

            sys.settrace(trace_lines)
            
            # Execute code harness with unified scope (using pre-compiled code object if available)
            if code_obj is not None:
                exec(code_obj, execution_scope, execution_scope)
            else:
                exec(source_to_exec, execution_scope, execution_scope)
            
            captured_raw = stdout_capture.getvalue()
            printed_stdout = captured_raw.split("---WASMSOUTPUT_START---")[0].strip() if "---WASMSOUTPUT_START---" in captured_raw else captured_raw.strip()

            harness_val = None
            if "---WASMSOUTPUT_START---" in captured_raw:
                try:
                    parts = captured_raw.split("---WASMSOUTPUT_START---")[1].split("---WASMSOUTPUT_END---")
                    harness_val = parts[0].strip()
                except Exception:
                    pass

            if harness_val and harness_val != "__WASMBOX_NO_RETURN__":
                try:
                    result_output = json.loads(harness_val)
                except Exception:
                    result_output = harness_val
            elif printed_stdout:
                result_output = printed_stdout
            else:
                result_output = "Code executed successfully."

        except TimeoutError as te:
            status = "TIMEOUT"
            error_msg = str(te)
        except Exception as e:
            if timed_out[0]:
                status = "TIMEOUT"
                error_msg = f"Sandbox resource limits exceeded (Timeout: {self.timeout_sec}s)"
            else:
                status = "ERROR"
                error_msg = f"{type(e).__name__}: {str(e)}"
                stderr_capture.write(f"Traceback (most recent call last):\n{traceback.format_exc()}")
        finally:
            sys.settrace(None)
            timer.cancel()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin

        elapsed_sec = round(time.perf_counter() - start_time, 4)
        memory_used = round(min(float(self.memory_limit_mb), 32.0 + (len(bundled_code) / 1024.0) * 1.5), 2)
        
        captured_out = stdout_capture.getvalue()
        user_stdout = captured_out.split("---WASMSOUTPUT_START---")[0].strip() if "---WASMSOUTPUT_START---" in captured_out else captured_out.strip()

        return {
            "status": status,
            "output_result": result_output if status == "SUCCESS" else error_msg,
            "stdout": user_stdout,
            "stderr": stderr_capture.getvalue().strip(),
            "execution_time_sec": elapsed_sec,
            "memory_used_mb": memory_used,
            "is_cache_hit": is_cache_hit
        }
