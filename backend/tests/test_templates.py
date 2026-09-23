import pytest
from app.pipeline.templates import STANDARD_TEMPLATES
from app.pipeline.validator import validate_python_code
from app.pipeline.compiler import PythonWasmCompiler
from app.sandbox.wasmtime_runner import WasmSandboxRunner

def test_all_standard_templates_pass_security_validation():
    """Verify that every standard plugin template passes strict AST validation."""
    for tpl in STANDARD_TEMPLATES:
        is_valid, violations = validate_python_code(tpl["code"])
        assert is_valid is True, f"Template {tpl['id']} failed AST validation: {violations}"
        assert len(violations) == 0

def test_json_masker_template_execution():
    """Test execution of PII & Secret Data Masker template."""
    runner = WasmSandboxRunner()
    tpl = next(t for t in STANDARD_TEMPLATES if t["id"] == "tpl-json-masker")
    bundled = PythonWasmCompiler.compile_plugin(tpl["code"], use_cache=False)
    
    input_payload = {
        "username": "alice",
        "password": "supersecretpassword123",
        "api_key": "sk-12345678",
        "profile": {"email": "alice@example.com", "token": "jwt-token-val"}
    }
    
    res = runner.execute(bundled, input_payload)
    assert res["status"] == "SUCCESS"
    out = res["output_result"]["sanitized_payload"]
    assert out["username"] == "alice"
    assert out["password"] == "********"
    assert out["api_key"] == "********"
    assert out["profile"]["token"] == "********"

def test_sha256_hasher_template_execution():
    """Test execution of Cryptographic SHA-256 Digest template."""
    runner = WasmSandboxRunner()
    tpl = next(t for t in STANDARD_TEMPLATES if t["id"] == "tpl-sha256-hasher")
    bundled = PythonWasmCompiler.compile_plugin(tpl["code"], use_cache=False)
    
    res = runner.execute(bundled, {"text": "wasmbox"})
    assert res["status"] == "SUCCESS"
    assert res["output_result"]["algorithm"] == "SHA-256"
    assert len(res["output_result"]["hash"]) == 64

def test_csv_to_json_template_execution():
    """Test execution of CSV to JSON Record Parser template."""
    runner = WasmSandboxRunner()
    tpl = next(t for t in STANDARD_TEMPLATES if t["id"] == "tpl-csv-json")
    bundled = PythonWasmCompiler.compile_plugin(tpl["code"], use_cache=False)
    
    csv_payload = "name,age,city\nAlice,30,Berlin\nBob,25,Tokyo"
    res = runner.execute(bundled, {"csv": csv_payload})
    assert res["status"] == "SUCCESS"
    assert res["output_result"]["record_count"] == 2
    assert res["output_result"]["records"][0]["name"] == "Alice"
    assert res["output_result"]["records"][1]["city"] == "Tokyo"

def test_regex_extractor_template_execution():
    """Test execution of Regex Entity & Token Extractor template."""
    runner = WasmSandboxRunner()
    tpl = next(t for t in STANDARD_TEMPLATES if t["id"] == "tpl-regex-extractor")
    bundled = PythonWasmCompiler.compile_plugin(tpl["code"], use_cache=False)
    
    text = "Contact support@wasmbox.io or dev@wasmbox.com, call 123-456-7890 or visit https://wasmbox.dev"
    res = runner.execute(bundled, {"text": text})
    assert res["status"] == "SUCCESS"
    assert "support@wasmbox.io" in res["output_result"]["emails"]
    assert "https://wasmbox.dev" in res["output_result"]["urls"]
    assert "123-456-7890" in res["output_result"]["phone_numbers"]

def test_stats_calculator_template_execution():
    """Test execution of Numeric Sequence Stats Engine template."""
    runner = WasmSandboxRunner()
    tpl = next(t for t in STANDARD_TEMPLATES if t["id"] == "tpl-stats-calc")
    bundled = PythonWasmCompiler.compile_plugin(tpl["code"], use_cache=False)
    
    res = runner.execute(bundled, [10, 20, 30, 40, 50])
    assert res["status"] == "SUCCESS"
    assert res["output_result"]["count"] == 5
    assert res["output_result"]["sum"] == 150
    assert res["output_result"]["mean"] == 30.0
    assert res["output_result"]["min"] == 10
    assert res["output_result"]["max"] == 50
