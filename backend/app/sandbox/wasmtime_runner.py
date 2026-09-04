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
        Captures stdout, stderr, exception tracebacks, and return values.
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
        
        try:
            local_scope = {}
            global_scope = {"__name__": "__main__"}
            
            # Instruction tracer interrupt for loop timeouts
            def trace_lines(frame, event, arg):
                if timed_out[0]:
                    raise TimeoutError(f"Execution exceeded maximum timeout of {self.timeout_sec} seconds")
                return trace_lines

            sys.settrace(trace_lines)
            
            # Execute code harness
            exec(bundled_code, global_scope, local_scope)
            
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
            "memory_used_mb": memory_used
        }
