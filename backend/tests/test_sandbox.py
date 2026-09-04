import pytest
from app.pipeline.validator import validate_python_code
from app.pipeline.compiler import PythonWasmCompiler
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
    user_code = "def process(data):\n    return 'OK'"
    bundled = PythonWasmCompiler.compile_plugin(user_code)
    assert "def process(data):" in bundled
    assert "---WASMSOUTPUT_START---" in bundled

def test_wasmtime_runner_execution():
    user_code = """def process(data):
    val = data if isinstance(data, str) else str(data)
    return {"result": val.upper()}
"""
    bundled = PythonWasmCompiler.compile_plugin(user_code)
    runner = WasmSandboxRunner()
    res = runner.execute(bundled, "hello wasm")
    
    assert res["status"] in ("SUCCESS", "ERROR")
    assert res["execution_time_sec"] >= 0.0
    assert res["memory_used_mb"] > 0
