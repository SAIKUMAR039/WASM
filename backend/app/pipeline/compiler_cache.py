import hashlib
import threading
from collections import OrderedDict
from typing import Optional

from app.pipeline.compiler import PythonWasmCompiler


class CompilerCache:
    """
    In-memory cache for compiled WasmBox execution harnesses.

    Same Python source code ko baar-baar compile karne se bachata hai.
    """

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    def _make_key(self, code: str) -> str:
        """Create a stable cache key from Python source code."""
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def get(self, code: str) -> Optional[str]:
        """Return cached compiled code, or None if not found."""
        key = self._make_key(code)

        with self._lock:
            if key not in self._cache:
                return None

            # Mark recently used
            self._cache.move_to_end(key)
            return self._cache[key]

    def compile(self, code: str) -> str:
        """
        Get compiled code from cache.
        If it is not cached, compile it and store the result.
        """
        cached = self.get(code)

        if cached is not None:
            return cached

        compiled = PythonWasmCompiler.compile_plugin(code)

        with self._lock:
            self._cache[key := self._make_key(code)] = compiled
            self._cache.move_to_end(key)

            # Remove oldest entry when cache is full
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

        return compiled

    def clear(self) -> None:
        """Clear all cached compiled code."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Return number of cached entries."""
        with self._lock:
            return len(self._cache)


# Shared application-level compiler cache
compiler_cache = CompilerCache(max_size=100)