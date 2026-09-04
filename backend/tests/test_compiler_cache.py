import io
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

from app.pipeline.cache import (
    WasmCompilerCache,
    CompiledWasmArtifact,
    parse_wasm_custom_sections,
    CorruptedCacheError,
    WASM_MAGIC,
    WASM_VERSION,
)
from app.pipeline.compiler import PythonWasmCompiler, WasmCompilationError
from app.pipeline.validator import validate_python_code, DISALLOWED_MODULES, FORBIDDEN_BUILTINS
from app.pipeline.package_manager import (
    WasmPackageManager,
    WheelSecurityError,
    WheelInfo,
)
from app.sandbox.wasmtime_runner import WasmSandboxRunner


# ---------------------------------------------------------------------------
# 1. Compiler Cache: Hit & Miss Tests
# ---------------------------------------------------------------------------

def test_compiler_cache_miss_then_hit(tmp_path):
    """Test that the first compile is a cache miss and the second is a cache hit."""
    cache_dir = tmp_path / "cache"
    custom_cache = WasmCompilerCache(cache_dir=str(cache_dir), enabled=True)

    original_cache = PythonWasmCompiler.cache
    PythonWasmCompiler.cache = custom_cache

    try:
        user_code = "def process(data):\n    return {'result': data.get('val', 0) * 10}"

        # First compilation: Cache Miss
        art1 = PythonWasmCompiler.compile_plugin(user_code, use_cache=True)
        assert art1.is_cache_hit is False
        assert art1.cache_key is not None
        cached_file = cache_dir / f"{art1.cache_key}.wasm"
        assert cached_file.exists()

        # Second compilation: Cache Hit
        art2 = PythonWasmCompiler.compile_plugin(user_code, use_cache=True)
        assert art2.is_cache_hit is True
        assert art2.cache_key == art1.cache_key
        assert art2.wasm_bytes == art1.wasm_bytes

        # Verify execution works identically with cached artifact
        runner = WasmSandboxRunner()
        res1 = runner.execute(art1, {"val": 5})
        res2 = runner.execute(art2, {"val": 5})

        assert res1["status"] == "SUCCESS"
        assert res2["status"] == "SUCCESS"
        assert res1["output_result"] == {"result": 50}
        assert res2["output_result"] == {"result": 50}
        assert res2["is_cache_hit"] is True

    finally:
        PythonWasmCompiler.cache = original_cache


def test_compiler_cache_miss_distinct_sources(tmp_path):
    """Test that distinct sources produce distinct cache keys and cache misses."""
    cache_dir = tmp_path / "cache"
    custom_cache = WasmCompilerCache(cache_dir=str(cache_dir), enabled=True)

    original_cache = PythonWasmCompiler.cache
    PythonWasmCompiler.cache = custom_cache

    try:
        code_a = "def process(data):\n    return 'AAA'"
        code_b = "def process(data):\n    return 'BBB'"

        art_a = PythonWasmCompiler.compile_plugin(code_a)
        art_b = PythonWasmCompiler.compile_plugin(code_b)

        assert art_a.is_cache_hit is False
        assert art_b.is_cache_hit is False
        assert art_a.cache_key != art_b.cache_key
        assert art_a.wasm_bytes != art_b.wasm_bytes
    finally:
        PythonWasmCompiler.cache = original_cache


# ---------------------------------------------------------------------------
# 2. Source & Configuration Invalidation Tests
# ---------------------------------------------------------------------------

def test_source_change_invalidation(tmp_path):
    """Test that modifying source code invalidates previous cache and recompiles."""
    cache_dir = tmp_path / "cache"
    custom_cache = WasmCompilerCache(cache_dir=str(cache_dir), enabled=True)

    original_cache = PythonWasmCompiler.cache
    PythonWasmCompiler.cache = custom_cache

    try:
        source_v1 = "def process(data):\n    return 'version_1'"
        art_v1 = PythonWasmCompiler.compile_plugin(source_v1)
        assert art_v1.is_cache_hit is False

        # Verify cache hit on source_v1
        art_v1_cached = PythonWasmCompiler.compile_plugin(source_v1)
        assert art_v1_cached.is_cache_hit is True

        # Modify source code
        source_v2 = "def process(data):\n    return 'version_2'"
        art_v2 = PythonWasmCompiler.compile_plugin(source_v2)
        assert art_v2.is_cache_hit is False
        assert art_v2.cache_key != art_v1.cache_key

        runner = WasmSandboxRunner()
        res = runner.execute(art_v2, None)
        assert res["output_result"] == "version_2"
    finally:
        PythonWasmCompiler.cache = original_cache


def test_build_config_invalidation(tmp_path):
    """Test that changing build configuration causes cache key invalidation."""
    cache_dir = tmp_path / "cache"
    cache = WasmCompilerCache(cache_dir=str(cache_dir), enabled=True)

    code = "def process(data):\n    return 42"
    key1 = cache.compute_cache_key(code, build_config={"opt": 1})
    key2 = cache.compute_cache_key(code, build_config={"opt": 2})

    assert key1 != key2


# ---------------------------------------------------------------------------
# 3. Corrupted Cache Recovery Tests
# ---------------------------------------------------------------------------

def test_corrupted_cache_truncated_file(tmp_path):
    """Test that a truncated or invalid header cache file is detected, safely deleted, and recompiled."""
    cache_dir = tmp_path / "cache"
    custom_cache = WasmCompilerCache(cache_dir=str(cache_dir), enabled=True)

    original_cache = PythonWasmCompiler.cache
    PythonWasmCompiler.cache = custom_cache

    try:
        code = "def process(data):\n    return 'corrupt_test'"
        art = PythonWasmCompiler.compile_plugin(code)
        cache_file = cache_dir / f"{art.cache_key}.wasm"
        assert cache_file.exists()

        # Corrupt the cache file by truncating to 3 bytes (invalid WASM header)
        cache_file.write_bytes(b"\x00as")

        # Cache get should safely catch corruption, purge file, and return None
        result = custom_cache.get(art.cache_key)
        assert result is None
        assert not cache_file.exists()
        assert custom_cache.stats["corrupted"] >= 1

        # Next compile_plugin call should recompile cleanly without crashing
        art_recompiled = PythonWasmCompiler.compile_plugin(code)
        assert art_recompiled.is_cache_hit is False
        assert cache_file.exists()
        assert len(cache_file.read_bytes()) > 100
    finally:
        PythonWasmCompiler.cache = original_cache


def test_corrupted_cache_corrupt_bytecode(tmp_path):
    """Test safe handling when custom section bytecode data is corrupted."""
    cache_dir = tmp_path / "cache"
    cache = WasmCompilerCache(cache_dir=str(cache_dir), enabled=True)

    # Construct invalid WASM binary with garbage in custom section
    from app.pipeline.cache import create_custom_section
    bad_wasm = WASM_MAGIC + WASM_VERSION + create_custom_section("wasmbox_bytecode", b"garbagedata")
    
    bad_file = cache_dir / "badkey.wasm"
    bad_file.write_bytes(bad_wasm)

    res = cache.get("badkey")
    assert res is None
    assert not bad_file.exists()  # Corrupt file must be safely removed


# ---------------------------------------------------------------------------
# 4. Safe Module Allowlist & Unsafe Module Rejection Tests
# ---------------------------------------------------------------------------

def test_safe_stdlib_modules_allowed():
    """Verify that all vetted safe standard library modules pass AST security validation and execute."""
    safe_snippets = [
        "import math\ndef process(data): return math.sqrt(16)",
        "import json\ndef process(data): return json.loads('{\"a\": 1}')",
        "import datetime\ndef process(data): return str(datetime.date(2026, 9, 4))",
        "import hashlib\ndef process(data): return hashlib.sha256(b'test').hexdigest()",
        "import collections\ndef process(data): return dict(collections.Counter('wasm'))",
        "import itertools\ndef process(data): return list(itertools.islice(range(10), 3))",
        "import functools\ndef process(data): return functools.reduce(lambda x, y: x + y, [1, 2, 3])",
        "import base64\ndef process(data): return base64.b64encode(b'wasm').decode()",
        "import zlib\ndef process(data): return len(zlib.compress(b'wasm'))",
        "import string\ndef process(data): return string.ascii_uppercase[:5]",
        "import copy\ndef process(data): return copy.deepcopy({'k': 'v'})",
        "import decimal\ndef process(data): return str(decimal.Decimal('3.14'))",
        "import uuid\ndef process(data): return len(str(uuid.uuid4()))",
        "import re\ndef process(data): return bool(re.match(r'^[a-z]+$', 'wasm'))",
        "import random\ndef process(data): return random.choice([1, 2, 3]) in [1, 2, 3]",
    ]

    runner = WasmSandboxRunner()
    for snippet in safe_snippets:
        is_valid, violations = validate_python_code(snippet)
        assert is_valid is True, f"Failed for snippet: {snippet}, violations: {violations}"
        
        bundled = PythonWasmCompiler.compile_plugin(snippet)
        res = runner.execute(bundled, None)
        assert res["status"] == "SUCCESS", f"Execution failed for snippet: {snippet}, err: {res.get('output_result')}"


def test_unsafe_modules_disallowed():
    """Verify that unsafe/native modules are strictly forbidden."""
    unsafe_modules = [
        "os", "sys", "subprocess", "ctypes", "socket", "http",
        "urllib", "requests", "shutil", "pathlib", "threading", "multiprocessing"
    ]

    for mod in unsafe_modules:
        code = f"import {mod}\ndef process(data): return 1"
        is_valid, violations = validate_python_code(code)
        assert is_valid is False, f"Module '{mod}' should have been disallowed"
        assert any(f"Forbidden module import: '{mod}'" in v for v in violations)


def test_forbidden_builtins_disallowed():
    """Verify that dangerous builtin calls are strictly blocked."""
    forbidden = ["eval('1+1')", "exec('a=1')", "__import__('os')", "open('foo.txt')"]
    for call in forbidden:
        code = f"def process(data):\n    {call}"
        is_valid, violations = validate_python_code(code)
        assert is_valid is False, f"Call '{call}' should have been blocked"


# ---------------------------------------------------------------------------
# 5. Pre-packaged Wheels & Package Manager Tests
# ---------------------------------------------------------------------------

def create_mock_pure_wheel(dest_dir: Path, name: str, version: str = "1.0.0", packages: list = None) -> Path:
    """Helper to build a valid pure-Python wheel for testing."""
    packages = packages or [name.replace("-", "_")]
    wheel_filename = f"{name}-{version}-py3-none-any.whl"
    wheel_path = dest_dir / wheel_filename

    with zipfile.ZipFile(wheel_path, "w") as zf:
        # Top-level packages
        for pkg in packages:
            zf.writestr(f"{pkg}/__init__.py", f"# {pkg} module\nVERSION = '{version}'\ndef get_val(): return 42\n")
        # Metadata
        dist_info = f"{name}-{version}.dist-info"
        zf.writestr(f"{dist_info}/METADATA", f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")
        zf.writestr(f"{dist_info}/WHEEL", "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
        zf.writestr(f"{dist_info}/top_level.txt", "\n".join(packages) + "\n")

    return wheel_path


def test_package_manager_inspect_and_allowlist(tmp_path):
    """Test package manager indexes safe pure-Python wheels and recognizes packages."""
    wheels_dir = tmp_path / "wheels"
    wheels_dir.mkdir()

    wheel_path = create_mock_pure_wheel(wheels_dir, "test_plugin_math", version="1.0.0", packages=["test_plugin_math"])
    
    pkg_manager = WasmPackageManager(wheels_dir=str(wheels_dir))
    info = pkg_manager.get_wheel("test_plugin_math")

    assert info is not None
    assert info.name == "test-plugin-math"
    assert info.is_pure_python is True
    assert info.is_safe is True
    assert "test_plugin_math" in info.top_level_packages

    # Check allowed packages
    allowed_pkgs = pkg_manager.get_allowed_packages()
    assert "test_plugin_math" in allowed_pkgs

    # Test AST validation with allowed packages
    code = "import test_plugin_math\ndef process(data): return test_plugin_math.get_val()"
    is_valid, violations = validate_python_code(code, allowed_packages=list(allowed_pkgs))
    assert is_valid is True
    assert len(violations) == 0


def test_package_manager_rejects_unsafe_native_wheel(tmp_path):
    """Test that wheels containing native binary extensions are rejected."""
    wheels_dir = tmp_path / "wheels"
    wheels_dir.mkdir()

    bad_wheel = wheels_dir / "native_pkg-1.0.0-cp312-cp312-win_amd64.whl"
    with zipfile.ZipFile(bad_wheel, "w") as zf:
        zf.writestr("native_pkg/__init__.py", "# native pkg")
        zf.writestr("native_pkg/native_core.pyd", b"FAKE_BINARY_PE_HEADER")

    pkg_manager = WasmPackageManager(wheels_dir=str(wheels_dir))
    with pytest.raises(WheelSecurityError) as exc_info:
        pkg_manager.inspect_wheel(str(bad_wheel))
    assert "contains unsafe native binary" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 6. build_plugin.py CLI Tests
# ---------------------------------------------------------------------------

def test_cli_build_valid_plugin(tmp_path):
    """Test build_plugin.py builds a valid .wasm artifact offline."""
    input_file = tmp_path / "my_plugin.py"
    output_wasm = tmp_path / "my_plugin.wasm"
    cache_dir = tmp_path / "cli_cache"

    input_file.write_text("def process(data):\n    return {'hello': data.upper()}\n", encoding="utf-8")

    from build_plugin import main as cli_main
    exit_code = cli_main([
        str(input_file),
        "-o", str(output_wasm),
        "--cache-dir", str(cache_dir),
        "--verbose"
    ])

    assert exit_code == 0
    assert output_wasm.exists()
    assert output_wasm.stat().st_size > 50

    # Verify WASM binary header and custom sections
    sections = parse_wasm_custom_sections(output_wasm.read_bytes())
    assert "wasmbox_metadata" in sections
    assert "wasmbox_bytecode" in sections
    assert "wasmbox_source" in sections


def test_cli_inspect_command(tmp_path, capsys):
    """Test build_plugin.py --inspect on an existing .wasm artifact."""
    input_file = tmp_path / "plugin.py"
    output_wasm = tmp_path / "plugin.wasm"
    input_file.write_text("print('cli test')\n", encoding="utf-8")

    from build_plugin import main as cli_main
    # 1. Build
    cli_main([str(input_file), "-o", str(output_wasm)])

    # 2. Inspect
    exit_code = cli_main(["--inspect", str(output_wasm)])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "WasmBox WASM Artifact Inspection" in captured.out
    assert "wasmbox_metadata" in captured.out
    assert "wasmbox_bytecode" in captured.out


def test_cli_clean_cache_command(tmp_path, capsys):
    """Test build_plugin.py --clean-cache."""
    cache_dir = tmp_path / "cache_to_clean"
    cache_dir.mkdir()
    (cache_dir / "test1.wasm").write_bytes(WASM_MAGIC + WASM_VERSION)

    from build_plugin import main as cli_main
    exit_code = cli_main(["--cache-dir", str(cache_dir), "--clean-cache"])
    assert exit_code == 0
    assert not (cache_dir / "test1.wasm").exists()

    captured = capsys.readouterr()
    assert "Purged 1 cached .wasm artifact(s)" in captured.out


def test_cli_missing_input_file(capsys):
    """Test build_plugin.py error handling for missing input file."""
    from build_plugin import main as cli_main
    exit_code = cli_main(["non_existent_file.py"])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_cli_security_validation_failure(tmp_path, capsys):
    """Test build_plugin.py fails clearly when input violates security rules."""
    unsafe_file = tmp_path / "unsafe.py"
    unsafe_file.write_text("import os\ndef process(data): os.system('whoami')\n", encoding="utf-8")

    from build_plugin import main as cli_main
    exit_code = cli_main([str(unsafe_file)])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Plugin failed security validation" in captured.err
    assert "Forbidden module import: 'os'" in captured.err
