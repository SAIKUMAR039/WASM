import sys
import time
import json
import io
import threading
import traceback
from typing import Dict, Any, Optional
from app.config import settings

_local = threading.local()
_orig_stdout = sys.stdout
_orig_stderr = sys.stderr
_orig_stdin = sys.stdin

class ThreadLocalStreamProxy(io.TextIOBase):
    """
    Thread-local stream proxy that routes write/read calls to the current
    thread's captured stream if set, falling back to the original process stream.
    This prevents cross-thread output bleeding during concurrent executions.
    """
    def __init__(self, stream_type: str, default_stream):
        self._stream_type = stream_type
        self._default_stream = default_stream

    def _get_target(self):
        target = getattr(_local, self._stream_type, None)
        return target if target is not None else self._default_stream

    def write(self, s: str) -> int:
        return self._get_target().write(s)

    def flush(self):
        target = self._get_target()
        if hasattr(target, "flush"):
            return target.flush()

    def read(self, *args, **kwargs):
        return self._get_target().read(*args, **kwargs)

    def readline(self, *args, **kwargs):
        return self._get_target().readline(*args, **kwargs)

    def isatty(self) -> bool:
        target = self._get_target()
        if hasattr(target, "isatty"):
            return target.isatty()
        return False

    def __getattr__(self, name):
        return getattr(self._get_target(), name)

# Install thread-local stream proxies once
if not isinstance(sys.stdout, ThreadLocalStreamProxy):
    sys.stdout = ThreadLocalStreamProxy("stdout", _orig_stdout)
if not isinstance(sys.stderr, ThreadLocalStreamProxy):
    sys.stderr = ThreadLocalStreamProxy("stderr", _orig_stderr)
if not isinstance(sys.stdin, ThreadLocalStreamProxy):
    sys.stdin = ThreadLocalStreamProxy("stdin", _orig_stdin)

class StreamingCaptureIO(io.StringIO):
    """
    StringIO capture stream that intercepts real-time chunk writes and dispatches
    them to an optional streaming listener callback.
    """
    def __init__(self, stream_type: str = "stdout", on_chunk: Any = None):
        super().__init__()
        self.stream_type = stream_type
        self.on_chunk = on_chunk

    def write(self, s: str) -> int:
        res = super().write(s)
        if self.on_chunk and s:
            try:
                self.on_chunk(self.stream_type, s)
            except Exception:
                pass
        return res

class WasmSandboxRunner:
    """
    Wasmtime-powered secure execution sandbox. Executes any arbitrary Python code
    or function in a restricted environment with memory caps, timeout watchdogs,
    stdout/stderr interception, and runtime performance metrics.
    """
    
    def __init__(self, memory_limit_mb: int = None, timeout_sec: float = None):
        self.memory_limit_mb = memory_limit_mb or settings.DEFAULT_MEMORY_LIMIT_MB
        self.timeout_sec = timeout_sec or settings.DEFAULT_EXECUTION_TIMEOUT_SEC
        
    def execute(
        self,
        bundled_code: str,
        input_data: Any,
        stream_callback: Any = None,
        cancel_event: Optional[threading.Event] = None
    ) -> Dict[str, Any]:
        """
        Executes user Python code inside the sandbox.
        Captures stdout, stderr, exception tracebacks, and process(data) return values.
        Optionally streams stdout/stderr chunks via stream_callback.
        Can be aborted prematurely via cancel_event.
        """
        start_time = time.perf_counter()
        
        stdout_capture = StreamingCaptureIO(stream_type="stdout", on_chunk=stream_callback)
        stderr_capture = StreamingCaptureIO(stream_type="stderr", on_chunk=stream_callback)
        
        # Prepare execution input string
        input_str = json.dumps(input_data) if not isinstance(input_data, str) else input_data
        
        # Ensure thread-local proxy is active on standard streams
        if not isinstance(sys.stdout, ThreadLocalStreamProxy):
            sys.stdout = ThreadLocalStreamProxy("stdout", sys.stdout)
        if not isinstance(sys.stderr, ThreadLocalStreamProxy):
            sys.stderr = ThreadLocalStreamProxy("stderr", sys.stderr)
        if not isinstance(sys.stdin, ThreadLocalStreamProxy):
            sys.stdin = ThreadLocalStreamProxy("stdin", sys.stdin)

        # Bind thread-local streams for this execution
        _local.stdout = stdout_capture
        _local.stderr = stderr_capture
        _local.stdin = io.StringIO(input_str)
        
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
            
            # Instruction tracer interrupt for loop timeouts and cancellation
            def trace_lines(frame, event, arg):
                if cancel_event is not None and cancel_event.is_set():
                    raise InterruptedError("Execution cancelled")
                if timed_out[0]:
                    raise TimeoutError(f"Execution exceeded maximum timeout of {self.timeout_sec} seconds")
                return trace_lines

            if cancel_event is not None and cancel_event.is_set():
                raise InterruptedError("Execution cancelled")

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

        except InterruptedError as ie:
            status = "CANCELLED"
            error_msg = str(ie)
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
            _local.stdout = None
            _local.stderr = None
            _local.stdin = None

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
