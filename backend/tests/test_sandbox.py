import pytest
from app.pipeline.validator import validate_python_code
from app.pipeline.compiler import PythonWasmCompiler
from app.pipeline.schema_validator import validate_json_payload
from app.pipeline.rate_limiter import RateLimiter
from app.sandbox.wasmtime_runner import WasmSandboxRunner

def test_ast_validator_safe_code():
    safe_code = """def process(data):\n    return {'output': data.get('val', 0) * 2}"""
    is_valid, violations = validate_python_code(safe_code)
    assert is_valid is True
    assert len(violations) == 0

def test_ast_validator_forbidden_import():
    unsafe_code = """import os\ndef process(data):\n    os.system('whoami')"""
    is_valid, violations = validate_python_code(unsafe_code)
    assert is_valid is False
    assert any("Forbidden module import" in v for v in violations)

def test_ast_validator_forbidden_builtin():
    unsafe_code = """def process(data):\n    eval('2 + 2')"""
    is_valid, violations = validate_python_code(unsafe_code)
    assert is_valid is False
    assert any("Forbidden builtin function call" in v for v in violations)

def test_compiler_harness():
    user_code = "print('Hello World')"
    bundled = PythonWasmCompiler.compile_plugin(user_code)
    assert "print('Hello World')" in bundled
    assert "---WASMSOUTPUT_START---" in bundled

def test_top_level_print_execution():
    user_code = "print('Hello World')"
    bundled = PythonWasmCompiler.compile_plugin(user_code)
    runner = WasmSandboxRunner()
    res = runner.execute(bundled, None)
    
    assert res["status"] == "SUCCESS"
    assert "Hello World" in str(res["output_result"])
    assert "Hello World" in res["stdout"]

def test_undefined_function_error_execution():
    invalid_code = 'python("Hello world")'
    bundled = PythonWasmCompiler.compile_plugin(invalid_code)
    runner = WasmSandboxRunner()
    res = runner.execute(bundled, None)
    
    assert res["status"] == "ERROR"
    assert "NameError" in res["output_result"]
    assert "name 'python' is not defined" in res["output_result"]
    assert "Traceback" in res["stderr"]

def test_process_function_with_dict_payload():
    user_code = """import datetime

def process(data):
    text = data.get("text", "Default Text") if isinstance(data, dict) else str(data)
    count = data.get("count", 1) if isinstance(data, dict) else 1
    return {
        "status": "PROCESSED",
        "uppercase_text": text.upper(),
        "repeated_text": text * count,
        "character_count": len(text)
    }
"""
    input_payload = {"text": "hello wasmbox", "count": 2}
    bundled = PythonWasmCompiler.compile_plugin(user_code)
    runner = WasmSandboxRunner()
    res = runner.execute(bundled, input_payload)

    assert res["status"] == "SUCCESS"
    assert isinstance(res["output_result"], dict)
    assert res["output_result"]["uppercase_text"] == "HELLO WASMBOX"
    assert res["output_result"]["character_count"] == 13

def test_json_schema_validator():
    schema = {"type": "object", "required": ["text", "count"]}
    valid_payload = {"text": "test", "count": 5}
    invalid_payload = {"text": "test"}

    ok, err = validate_json_payload(valid_payload, schema)
    assert ok is True

    ok2, err2 = validate_json_payload(invalid_payload, schema)
    assert ok2 is False
    assert "Missing required payload keys" in err2

def test_tenant_rate_limiter():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    ok1, rem1 = limiter.check_rate_limit("tenant_test")
    assert ok1 is True
    assert rem1 == 1

    ok2, rem2 = limiter.check_rate_limit("tenant_test")
    assert ok2 is True
    assert rem2 == 0

    ok3, rem3 = limiter.check_rate_limit("tenant_test")
    assert ok3 is False
    assert rem3 == 0

def test_memory_growth_and_leak_detection():
    runner = WasmSandboxRunner(memory_limit_mb=64)
    # Code with loop creating large arrays to trigger memory growth heuristics
    memory_code = """def process(data):
    arr = [x * 2 for x in range(15000)]
    return len(arr)
"""
    bundled = PythonWasmCompiler.compile_plugin(memory_code)
    res = runner.execute(bundled, None)
    assert res["status"] == "SUCCESS"
    assert res["memory_used_mb"] >= 24.5
    assert "peak_memory_mb" in res
    assert res["peak_memory_mb"] >= res["memory_used_mb"]

def test_sandboxed_environment_variables():
    runner = WasmSandboxRunner()
    code = """def process(data):
    api_key = wasmbox_getenv("API_KEY", "default-key")
    region = wasmbox_getenv("REGION", "us-east-1")
    return {"api_key": api_key, "region": region}
"""
    bundled = PythonWasmCompiler.compile_plugin(
        code,
        env_vars={"API_KEY": "secret-token-xyz", "REGION": "eu-central-1", "PATH": "malicious"}
    )
    res = runner.execute(bundled, None)
    assert res["status"] == "SUCCESS"
    assert res["output_result"]["api_key"] == "secret-token-xyz"
    assert res["output_result"]["region"] == "eu-central-1"

def test_benchmark_calculation_metrics():
    runner = WasmSandboxRunner()
    code = "def process(data): return 42"
    bundled = PythonWasmCompiler.compile_plugin(code)
    
    lats = []
    for _ in range(5):
        res = runner.execute(bundled, None)
        assert res["status"] == "SUCCESS"
        lats.append(res["execution_time_ms"])
    
    assert len(lats) == 5
    assert all(l > 0 for l in lats)

def test_concurrent_sandbox_executions():
    """Verify thread-local stream isolation during concurrent plugin runs."""
    import concurrent.futures

    runner = WasmSandboxRunner()
    code1 = "def process(data): return f'thread_1_{data}'"
    code2 = "def process(data): return f'thread_2_{data}'"
    b1 = PythonWasmCompiler.compile_plugin(code1, use_cache=False)
    b2 = PythonWasmCompiler.compile_plugin(code2, use_cache=False)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(runner.execute, b1, "A")
        f2 = executor.submit(runner.execute, b2, "B")
        r1 = f1.result()
        r2 = f2.result()

    assert r1["status"] == "SUCCESS"
    assert r2["status"] == "SUCCESS"
    assert r1["output_result"] == "thread_1_A"
    assert r2["output_result"] == "thread_2_B"




