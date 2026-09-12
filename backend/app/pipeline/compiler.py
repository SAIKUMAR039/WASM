import hashlib
import json
import marshal
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.config import settings
from app.pipeline.cache import (
    WasmCompilerCache,
    CompiledWasmArtifact,
    get_compiler_cache,
    create_custom_section,
    WASM_MAGIC,
    WASM_VERSION,
    COMPILER_VERSION,
)
from app.pipeline.package_manager import (
    WasmPackageManager,
    get_package_manager
)

class WasmCompilationError(Exception):
    pass

class PythonWasmCompiler:
    """
    Transforms user-provided Python code into an execution harness module.
    Supports pre-compiled .wasm bytecode caching for faster execution,
    automatic re-compilation on source/config changes, and pre-packaged wheels.
    """
    
    cache: WasmCompilerCache = get_compiler_cache()
    package_manager: WasmPackageManager = get_package_manager()

    ENTRY_HARNESS_TEMPLATE = """# WasmBox Generated Execution Harness
import json
import sys
import math
import re
import datetime
import random
import hashlib
import collections
import itertools
import functools
import base64
import zlib
import string
import copy
import decimal
import uuid

# --- USER PLUGIN CODE START ---
{user_code}
# --- USER PLUGIN CODE END ---

def _wasmbox_main(raw_input_json):
    data = None
    if raw_input_json:
        try:
            data = json.loads(raw_input_json)
        except Exception:
            data = raw_input_json

    target_func = None
    if 'process' in globals() and callable(globals()['process']):
        target_func = globals()['process']
    elif 'main' in globals() and callable(globals()['main']):
        target_func = globals()['main']
    elif 'process' in locals() and callable(locals()['process']):
        target_func = locals()['process']
    elif 'main' in locals() and callable(locals()['main']):
        target_func = locals()['main']

    res = None
    if target_func:
        res = target_func(data)

    if res is not None:
        try:
            return json.dumps(res)
        except Exception:
            return str(res)
    return "__WASMBOX_NO_RETURN__"

if __name__ == "__main__":
    input_str = sys.stdin.read() if not sys.stdin.isatty() else ""
    out = _wasmbox_main(input_str)
    print("---WASMSOUTPUT_START---")
    print(out)
    print("---WASMSOUTPUT_END---")
"""

    @classmethod
    def get_cache(cls) -> WasmCompilerCache:
        """Returns the active compiler cache instance."""
        return cls.cache

    @classmethod
    def get_package_manager(cls) -> WasmPackageManager:
        """Returns the active package manager instance."""
        return cls.package_manager

    @classmethod
    def compile_plugin(
        cls,
        code: str,
        use_cache: bool = True,
        build_config: Optional[Dict[str, Any]] = None,
        wheels: Optional[List[str]] = None
    ) -> CompiledWasmArtifact:
        """
        Compiles user python code into the Wasm execution harness and pre-compiled bytecode.
        Uses cached .wasm bytecode if available and valid; otherwise compiles fresh,
        saves to cache, and returns the CompiledWasmArtifact.
        """
        if not code or not code.strip():
            raise WasmCompilationError("Code snippet cannot be empty")

        cache_key = cls.cache.compute_cache_key(code, build_config=build_config, wheels=wheels)

        # 1. Check compiler cache
        if use_cache and cls.cache.enabled:
            cached = cls.cache.get(cache_key)
            if cached is not None:
                return cached

        # 2. Build harness source
        try:
            harness_code = cls.ENTRY_HARNESS_TEMPLATE.format(user_code=code)
        except Exception as e:
            raise WasmCompilationError(f"Failed to generate execution harness: {e}")

        # 3. Pre-compile into Python bytecode code object
        try:
            code_obj = compile(harness_code, "<wasm_harness>", "exec")
            bytecode = marshal.dumps(code_obj)
        except SyntaxError as se:
            raise WasmCompilationError(f"Syntax error compiling plugin: {se.msg} at line {se.lineno}")
        except Exception as e:
            raise WasmCompilationError(f"Compilation error: {e}")

        # 4. Construct WebAssembly binary module with custom sections
        metadata = {
            "cache_key": cache_key,
            "compiler_version": COMPILER_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_hash": hashlib.sha256(code.strip().encode("utf-8")).hexdigest(),
            "build_config": build_config or {},
            "wheels": wheels or []
        }

        wasm_header = WASM_MAGIC + WASM_VERSION
        sec_meta = create_custom_section("wasmbox_metadata", json.dumps(metadata).encode("utf-8"))
        sec_code = create_custom_section("wasmbox_bytecode", bytecode)
        sec_source = create_custom_section("wasmbox_source", harness_code.encode("utf-8"))
        sec_wheels = create_custom_section("wasmbox_wheels", json.dumps(wheels or []).encode("utf-8"))
        wasm_bytes = wasm_header + sec_meta + sec_code + sec_source + sec_wheels

        artifact = CompiledWasmArtifact(
            harness_code=harness_code,
            wasm_bytes=wasm_bytes,
            cache_key=cache_key,
            is_cache_hit=False,
            metadata=metadata,
            code_object=code_obj
        )

        # 5. Persist to cache
        if use_cache and cls.cache.enabled:
            cls.cache.put(cache_key, artifact)

        return artifact

    @classmethod
    def compile_to_wasm_file(
        cls,
        code: str,
        output_path: str,
        use_cache: bool = True,
        build_config: Optional[Dict[str, Any]] = None,
        wheels: Optional[List[str]] = None
    ) -> CompiledWasmArtifact:
        """
        Compiles user code and writes the resulting .wasm binary artifact to output_path.
        """
        artifact = cls.compile_plugin(
            code=code,
            use_cache=use_cache,
            build_config=build_config,
            wheels=wheels
        )
        artifact.save(output_path)
        return artifact

