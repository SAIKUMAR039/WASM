#!/usr/bin/env python3
"""
WasmBox Offline Plugin Builder CLI
Compiles Python plugins into pre-compiled WebAssembly (.wasm) binary artifacts
with embedded bytecode and metadata, completely offline without requiring network access.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add backend to sys.path so app modules are available
backend_dir = Path(__file__).resolve().parent / "backend"
if backend_dir.exists() and str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from app.pipeline.compiler import PythonWasmCompiler, WasmCompilationError
    from app.pipeline.validator import validate_python_code
    from app.pipeline.cache import (
        WasmCompilerCache,
        CompiledWasmArtifact,
        parse_wasm_custom_sections,
        CorruptedCacheError,
    )
    from app.pipeline.package_manager import WasmPackageManager
    from app.config import settings
except ImportError as e:
    sys.stderr.write(f"Error: Failed to import WasmBox pipeline modules: {e}\n")
    sys.exit(1)


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        prog="build_plugin.py",
        description="Compile Python plugins into WebAssembly (.wasm) bytecode artifacts offline."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Path to the input Python plugin source file (.py)"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output",
        help="Destination path for the compiled .wasm artifact (default: <input_stem>.wasm)"
    )
    parser.add_argument(
        "--cache-dir",
        dest="cache_dir",
        default=None,
        help="Directory to use for pre-compiled .wasm bytecode cache (default: .wasmbox_cache)"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass compiler cache and force re-compilation"
    )
    parser.add_argument(
        "--clean-cache",
        action="store_true",
        help="Purge all cached .wasm artifacts from the cache directory and exit"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip AST security validation against disallowed modules"
    )
    parser.add_argument(
        "-w", "--wheel",
        action="append",
        dest="wheels",
        default=[],
        help="Pre-packaged .whl file to register/attach to the plugin build (can be repeated)"
    )
    parser.add_argument(
        "--inspect",
        metavar="WASM_FILE",
        help="Inspect an existing .wasm artifact and print its metadata, sections, and cache key"
    )
    parser.add_argument(
        "--list-wheels",
        action="store_true",
        help="List all discovered pre-packaged wheels in the wheels repository and exit"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print verbose build, cache, and timing diagnostics"
    )

    return parser.parse_args(args)


def inspect_wasm_file(wasm_path_str: str) -> int:
    path = Path(wasm_path_str)
    if not path.exists():
        sys.stderr.write(f"Error: File not found: '{wasm_path_str}'\n")
        return 1

    try:
        with open(path, "rb") as f:
            data = f.read()
        sections = parse_wasm_custom_sections(data)
    except Exception as e:
        sys.stderr.write(f"Error: Failed to inspect '{wasm_path_str}': {e}\n")
        return 1

    print(f"=== WasmBox WASM Artifact Inspection ===")
    print(f"File:           {path.resolve()}")
    print(f"File Size:      {len(data):,} bytes")
    print(f"Header:         WASM 1.0 (\\x00asm \\x01\\x00\\x00\\x00)")
    print(f"Total Sections: {len(sections)}")

    for sec_name, sec_bytes in sections.items():
        print(f"\n  Section '{sec_name}': {len(sec_bytes):,} bytes")
        if sec_name == "wasmbox_metadata":
            try:
                meta = json.loads(sec_bytes.decode("utf-8"))
                print(f"    Compiler Version: {meta.get('compiler_version')}")
                print(f"    Cache Key:        {meta.get('cache_key')}")
                print(f"    Source Hash:      {meta.get('source_hash')}")
                print(f"    Created At:       {meta.get('created_at')}")
                if meta.get("wheels"):
                    print(f"    Wheels:           {meta.get('wheels')}")
            except Exception:
                pass
        elif sec_name == "wasmbox_source":
            preview = sec_bytes.decode("utf-8", errors="replace").strip()
            preview_lines = preview.splitlines()[:5]
            print("    Source Preview:")
            for line in preview_lines:
                print(f"      | {line}")
            if len(preview.splitlines()) > 5:
                print(f"      ... ({len(preview.splitlines()) - 5} more lines)")

    return 0


def main(args=None) -> int:
    parsed = parse_args(args)

    # Initialize cache & package manager
    cache_dir = parsed.cache_dir or settings.CACHE_DIR
    cache = WasmCompilerCache(cache_dir=cache_dir, enabled=not parsed.no_cache)
    pkg_manager = WasmPackageManager()

    # Handle --clean-cache
    if parsed.clean_cache:
        count = cache.clear()
        print(f"[CACHE] Purged {count} cached .wasm artifact(s) from '{cache.cache_dir}'.")
        return 0

    # Handle --list-wheels
    if parsed.list_wheels:
        wheels = pkg_manager.list_available_wheels()
        print(f"=== Pre-packaged Wheels in '{pkg_manager.wheels_dir}' ===")
        if not wheels:
            print("  (No wheels currently registered)")
        for w in wheels:
            status = "SAFE" if w.is_safe else "UNSAFE"
            print(f"  - {w.name} v{w.version} [{status}] ({w.filename}) -> Packages: {', '.join(w.top_level_packages)}")
        return 0

    # Handle --inspect
    if parsed.inspect:
        return inspect_wasm_file(parsed.inspect)

    # Require input file for building
    if not parsed.input:
        sys.stderr.write("Error: Missing input Python source file. Use --help for usage.\n")
        return 2

    input_path = Path(parsed.input)
    if not input_path.exists():
        sys.stderr.write(f"Error: Input file '{parsed.input}' does not exist.\n")
        return 1

    try:
        source_code = input_path.read_text(encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"Error: Unable to read input file '{parsed.input}': {e}\n")
        return 1

    if not source_code.strip():
        sys.stderr.write(f"Error: Input file '{parsed.input}' is empty.\n")
        return 1

    # Register any command-line wheels
    attached_wheels = []
    if parsed.wheels:
        for wheel_path in parsed.wheels:
            try:
                winfo = pkg_manager.register_wheel(wheel_path)
                attached_wheels.append(winfo.name)
                if parsed.verbose:
                    print(f"[WHEEL] Registered safe wheel: {winfo.name} ({winfo.filename})")
            except Exception as e:
                sys.stderr.write(f"Error: Failed to register wheel '{wheel_path}': {e}\n")
                return 1

    # Perform AST Security Validation
    if not parsed.no_validate:
        allowed_pkgs = list(pkg_manager.get_allowed_packages())
        is_valid, violations = validate_python_code(source_code, allowed_packages=allowed_pkgs)
        if not is_valid:
            sys.stderr.write("Error: Plugin failed security validation:\n")
            for violation in violations:
                sys.stderr.write(f"  - {violation}\n")
            return 1

    # Determine destination output path
    if parsed.output:
        out_path = Path(parsed.output)
    else:
        out_path = input_path.with_suffix(".wasm")

    # Configure compiler to use custom cache/pkg_manager if provided
    original_cache = PythonWasmCompiler.cache
    PythonWasmCompiler.cache = cache

    t_start = time.perf_counter()
    try:
        artifact = PythonWasmCompiler.compile_plugin(
            source_code,
            use_cache=not parsed.no_cache,
            wheels=attached_wheels
        )
        artifact.save(str(out_path))
    except WasmCompilationError as ce:
        sys.stderr.write(f"Error: Compilation failed: {ce}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Error: Unexpected build failure: {e}\n")
        return 1
    finally:
        PythonWasmCompiler.cache = original_cache

    t_elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)

    cache_status = "CACHE HIT" if artifact.is_cache_hit else "CACHE MISS (Compiled & Cached)"
    if parsed.no_cache:
        cache_status = "BYPASSED (--no-cache)"

    print(f"[SUCCESS] Built plugin into WebAssembly artifact:")
    print(f"  Input:        {input_path}")
    print(f"  Output:       {out_path.resolve()}")
    print(f"  Artifact Size: {len(artifact.wasm_bytes):,} bytes")
    print(f"  Cache Status: {cache_status}")
    print(f"  Cache Key:    {artifact.cache_key}")
    print(f"  Build Time:   {t_elapsed_ms} ms")

    if parsed.verbose and artifact.metadata:
        print(f"  Metadata:     {json.dumps(artifact.metadata, indent=2)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
