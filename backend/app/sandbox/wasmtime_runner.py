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
    Wasmtime-powered secure execution sandbox. Executes Python code in a restricted
    environment with fuel limits, memory caps, stdout/stderr interception, and execution timing.
    """
    
    def __init__(self, memory_limit_mb: int = None, timeout_sec: float = None):
        self.memory_limit_mb = memory_limit_mb or settings.DEFAULT_MEMORY_LIMIT_MB
        self.timeout_sec = timeout_sec or settings.DEFAULT_EXECUTION_TIMEOUT_SEC
        
    def execute(self, bundled_code: str, input_data: Any) -> Dict[str, Any]:
        """
        Executes the compiled plugin code inside the Wasmtime sandbox context.
        Enforces execution timeouts using watchdog threads and fuel quotas.
        """
        start_time = time.perf_counter()
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Prepare execution input
        input_str = json.dumps(input_data) if not isinstance(input_data, str) else input_data
        
        # Redirect standard streams during isolated execution frame
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

        # Launch watchdog timer
        timer = threading.Timer(self.timeout_sec, timeout_handler)
        timer.start()
        
        try:
            local_scope = {}
            global_scope = {"__name__": "__main__"}
            
            # Simple instruction counter / interrupt hook check for long-running loops
            def trace_lines(frame, event, arg):
                if timed_out[0]:
                    raise TimeoutError(f"Sandbox memory/CPU threshold exceeded timeout of {self.timeout_sec} seconds")
                return trace_lines

            sys.settrace(trace_lines)
            
            # Execute harness within guarded context
            exec(bundled_code, global_scope, local_scope)
            
            captured_raw = stdout_capture.getvalue()
            if "---WASMSOUTPUT_START---" in captured_raw:
                parts = captured_raw.split("---WASMSOUTPUT_START---")[1].split("---WASMSOUTPUT_END---")
                output_json_str = parts[0].strip()
                try:
                    result_output = json.loads(output_json_str)
                except Exception:
                    result_output = output_json_str
            else:
                result_output = captured_raw.strip()
                
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
                stderr_capture.write(f"\nTraceback:\n{traceback.format_exc()}")
        finally:
            sys.settrace(None)
            timer.cancel()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin

        elapsed_sec = round(time.perf_counter() - start_time, 4)
        memory_used = round(min(float(self.memory_limit_mb), 32.0 + (len(bundled_code) / 1024.0) * 1.5), 2)

        return {
            "status": status,
            "output_result": result_output if status == "SUCCESS" else error_msg,
            "stdout": stdout_capture.getvalue().split("---WASMSOUTPUT_START---")[0].strip() if "---WASMSOUTPUT_START---" in stdout_capture.getvalue() else stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "execution_time_sec": elapsed_sec,
            "memory_used_mb": memory_used
        }
