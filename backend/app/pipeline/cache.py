import hashlib
import io
import json
import marshal
import os
import sys
import tempfile
import types
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from app.config import settings

WASM_MAGIC = b"\x00asm"
WASM_VERSION = b"\x01\x00\x00\x00"
COMPILER_VERSION = "1.0.0"

class CorruptedCacheError(Exception):
    """Raised when a cached WASM artifact is damaged, truncated, or unreadable."""
    pass

def encode_u32_leb128(val: int) -> bytes:
    """Encodes an unsigned 32-bit integer into LEB128 format."""
    res = bytearray()
    while True:
        byte = val & 0x7F
        val >>= 7
        if val != 0:
            byte |= 0x80
        res.append(byte)
        if val == 0:
            break
    return bytes(res)

def decode_u32_leb128(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decodes an unsigned LEB128 integer from data starting at offset."""
    res = 0
    shift = 0
    curr = offset
    while True:
        if curr >= len(data):
            raise CorruptedCacheError("Unexpected end of data while decoding LEB128")
        byte = data[curr]
        curr += 1
        res |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    return res, curr

def create_custom_section(name: str, payload: bytes) -> bytes:
    """Creates a standard WebAssembly Custom Section (Section ID 0)."""
    name_bytes = name.encode("utf-8")
    name_len_leb = encode_u32_leb128(len(name_bytes))
    section_payload = name_len_leb + name_bytes + payload
    section_len_leb = encode_u32_leb128(len(section_payload))
    return b"\x00" + section_len_leb + section_payload

def parse_wasm_custom_sections(wasm_bytes: bytes) -> Dict[str, bytes]:
    """
    Parses a WebAssembly binary and extracts all custom sections.
    Raises CorruptedCacheError if header, section bounds, or LEB128 lengths are invalid.
    """
    if len(wasm_bytes) < 8:
        raise CorruptedCacheError("WASM binary is smaller than the 8-byte header")
    if wasm_bytes[:4] != WASM_MAGIC or wasm_bytes[4:8] != WASM_VERSION:
        raise CorruptedCacheError("Invalid WebAssembly header magic or version")

    sections: Dict[str, bytes] = {}
    offset = 8
    while offset < len(wasm_bytes):
        sec_id = wasm_bytes[offset]
        offset += 1
        try:
            sec_size, offset = decode_u32_leb128(wasm_bytes, offset)
        except Exception as e:
            raise CorruptedCacheError(f"Failed to decode section size: {e}")

        sec_end = offset + sec_size
        if sec_end > len(wasm_bytes):
            raise CorruptedCacheError("Section boundary extends past the end of the file")

        if sec_id == 0:  # Custom section
            try:
                name_len, name_offset = decode_u32_leb128(wasm_bytes, offset)
                name_end = name_offset + name_len
                if name_end > sec_end:
                    raise CorruptedCacheError("Custom section name extends beyond section body")
                sec_name = wasm_bytes[name_offset:name_end].decode("utf-8", errors="replace")
                payload = wasm_bytes[name_end:sec_end]
                sections[sec_name] = payload
            except Exception as e:
                raise CorruptedCacheError(f"Failed to parse custom section: {e}")

        offset = sec_end

    return sections

class CompiledWasmArtifact(str):
    """
    Represents a compiled WebAssembly execution artifact.
    Inherits from str so it drops into existing string-based execution harnesses,
    while carrying binary bytecode, metadata, and cache status.
    """

    def __new__(
        cls,
        harness_code: str,
        wasm_bytes: bytes,
        cache_key: str,
        is_cache_hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        code_object: Optional[types.CodeType] = None
    ):
        instance = super().__new__(cls, harness_code)
        instance.wasm_bytes = wasm_bytes
        instance.cache_key = cache_key
        instance.is_cache_hit = is_cache_hit
        instance.metadata = metadata or {}
        instance._code_object = code_object
        return instance

    @property
    def code_object(self) -> types.CodeType:
        """Lazily deserializes the compiled Python code object from bytecode if needed."""
        if self._code_object is None:
            if hasattr(self, "wasm_bytes") and self.wasm_bytes:
                sections = parse_wasm_custom_sections(self.wasm_bytes)
                bytecode = sections.get("wasmbox_bytecode")
                if bytecode:
                    self._code_object = marshal.loads(bytecode)
            if self._code_object is None:
                self._code_object = compile(str(self), "<wasm_harness>", "exec")
        return self._code_object

    def save(self, file_path: str):
        """Saves the compiled WebAssembly binary artifact to a file."""
        out_path = Path(file_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(self.wasm_bytes)

    @classmethod
    def from_wasm_bytes(
        cls,
        data: bytes,
        cache_key: str = "",
        is_cache_hit: bool = False
    ) -> "CompiledWasmArtifact":
        """Reconstructs a CompiledWasmArtifact from raw .wasm binary bytes."""
        sections = parse_wasm_custom_sections(data)
        
        meta_raw = sections.get("wasmbox_metadata")
        if not meta_raw:
            raise CorruptedCacheError("Missing wasmbox_metadata custom section")
        try:
            metadata = json.loads(meta_raw.decode("utf-8"))
        except Exception as e:
            raise CorruptedCacheError(f"Corrupted metadata JSON in custom section: {e}")

        source_raw = sections.get("wasmbox_source")
        if not source_raw:
            raise CorruptedCacheError("Missing wasmbox_source custom section")
        harness_code = source_raw.decode("utf-8", errors="replace")

        bytecode_raw = sections.get("wasmbox_bytecode")
        if not bytecode_raw:
            raise CorruptedCacheError("Missing wasmbox_bytecode custom section")
        try:
            code_obj = marshal.loads(bytecode_raw)
            if not isinstance(code_obj, types.CodeType):
                raise CorruptedCacheError(f"Deserialized bytecode is {type(code_obj)}, expected CodeType")
        except CorruptedCacheError:
            raise
        except Exception as e:
            raise CorruptedCacheError(f"Corrupted Python bytecode in custom section: {e}")

        key = cache_key or metadata.get("cache_key", "")
        return cls(
            harness_code=harness_code,
            wasm_bytes=data,
            cache_key=key,
            is_cache_hit=is_cache_hit,
            metadata=metadata,
            code_object=code_obj
        )

    @classmethod
    def from_wasm_file(
        cls,
        file_path: str,
        cache_key: str = "",
        is_cache_hit: bool = False
    ) -> "CompiledWasmArtifact":
        """Loads and validates a CompiledWasmArtifact from a .wasm file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"WASM file not found: {file_path}")
        with open(path, "rb") as f:
            data = f.read()
        return cls.from_wasm_bytes(data, cache_key=cache_key, is_cache_hit=is_cache_hit)

class WasmCompilerCache:
    """
    Manages pre-compiled WebAssembly bytecode cache storage, retrieval,
    hashing, and corrupted cache recovery.
    """

    def __init__(self, cache_dir: Optional[str] = None, enabled: bool = True):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(settings.CACHE_DIR)
        if not self.cache_dir.is_absolute():
            self.cache_dir = Path.cwd() / self.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.enabled = enabled if enabled is not None else settings.ENABLE_COMPILER_CACHE
        self.stats = {"hits": 0, "misses": 0, "corrupted": 0, "writes": 0}

    def compute_cache_key(
        self,
        source_code: str,
        build_config: Optional[Dict[str, Any]] = None,
        wheels: Optional[List[str]] = None
    ) -> str:
        """
        Computes a deterministic SHA-256 cache key based on:
        - Source code content
        - Build configuration (compiler flags, allowed modules)
        - Attached wheel dependencies
        - Compiler and Python runtime versions
        """
        hasher = hashlib.sha256()
        # 1. Source code (normalized trailing whitespace)
        hasher.update(source_code.strip().encode("utf-8"))
        # 2. Build configuration
        config_data = build_config.copy() if build_config else {}
        config_json = json.dumps(config_data, sort_keys=True)
        hasher.update(config_json.encode("utf-8"))
        # 3. Wheels / dependencies
        if wheels:
            wheels_json = json.dumps(sorted(wheels))
            hasher.update(wheels_json.encode("utf-8"))
        # 4. Compiler & Python version
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        hasher.update(f"{COMPILER_VERSION}:{py_ver}".encode("utf-8"))

        return hasher.hexdigest()

    def get_artifact_path(self, cache_key: str) -> Path:
        """Returns the file path for a given cache key."""
        return self.cache_dir / f"{cache_key}.wasm"

    def has(self, cache_key: str) -> bool:
        """Checks if a valid, uncorrupted cached artifact exists."""
        artifact_path = self.get_artifact_path(cache_key)
        if not artifact_path.exists():
            return False
        try:
            CompiledWasmArtifact.from_wasm_file(str(artifact_path), cache_key=cache_key)
            return True
        except Exception:
            return False

    def get(self, cache_key: str) -> Optional[CompiledWasmArtifact]:
        """
        Retrieves a cached WASM artifact.
        Handles cache misses and safely removes corrupted cache files.
        """
        if not self.enabled:
            self.stats["misses"] += 1
            return None

        artifact_path = self.get_artifact_path(cache_key)
        if not artifact_path.exists():
            self.stats["misses"] += 1
            return None

        try:
            artifact = CompiledWasmArtifact.from_wasm_file(
                str(artifact_path),
                cache_key=cache_key,
                is_cache_hit=True
            )
            self.stats["hits"] += 1
            return artifact
        except (CorruptedCacheError, Exception) as e:
            # Corrupted cache file detected: safely purge it and treat as cache miss
            self.stats["corrupted"] += 1
            self.stats["misses"] += 1
            try:
                if artifact_path.exists():
                    artifact_path.unlink()
            except OSError:
                pass
            return None

    def put(self, cache_key: str, artifact: CompiledWasmArtifact) -> str:
        """
        Atomically saves a compiled WASM artifact into the cache directory.
        Returns the absolute file path of the saved artifact.
        """
        if not self.enabled:
            return ""

        artifact_path = self.get_artifact_path(cache_key)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Write to temporary file in same directory first to guarantee atomic write on rename
        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(self.cache_dir), prefix="tmp_wasm_", suffix=".tmp")
        try:
            with open(tmp_fd, "wb") as f:
                f.write(artifact.wasm_bytes)
            # Replace target file atomically
            os.replace(tmp_path, str(artifact_path))
            self.stats["writes"] += 1
            return str(artifact_path.resolve())
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def invalidate(self, cache_key: str) -> bool:
        """Removes a specific cache artifact."""
        artifact_path = self.get_artifact_path(cache_key)
        if artifact_path.exists():
            artifact_path.unlink()
            return True
        return False

    def clear(self) -> int:
        """Purges all cached WASM artifacts in the cache directory."""
        count = 0
        if not self.cache_dir.exists():
            return count
        for item in self.cache_dir.glob("*.wasm"):
            try:
                item.unlink()
                count += 1
            except OSError:
                pass
        return count

_default_cache: Optional[WasmCompilerCache] = None

def get_compiler_cache() -> WasmCompilerCache:
    global _default_cache
    if _default_cache is None:
        _default_cache = WasmCompilerCache()
    return _default_cache
