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
