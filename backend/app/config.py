from pydantic_settings import BaseSettings
from pydantic import ConfigDict

SAFE_STDLIB_MODULES = [
    # Core formats & encoding
    "json", "base64", "zlib", "csv", "struct",
    # Math & numbers
    "math", "cmath", "decimal", "fractions", "numbers", "statistics", "random",
    # Text processing
    "re", "string", "unicodedata", "difflib", "textwrap",
    # Collections & functional
    "collections", "itertools", "functools", "operator", "bisect", "heapq", "array",
    # Types & data structures
    "typing", "dataclasses", "enum", "copy",
    # Safe utilities
    "datetime", "time", "uuid", "hashlib", "ipaddress",
]

class Settings(BaseSettings):
    PROJECT_NAME: str = "WasmBox"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    
    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://localhost:27017/wasm"
    MONGODB_DB_NAME: str = "wasm"
    
    # Sandbox Default Resource Limits
    DEFAULT_MEMORY_LIMIT_MB: int = 128
    DEFAULT_EXECUTION_TIMEOUT_SEC: float = 5.0
    DEFAULT_MAX_FUEL: int = 100_000_000
    
    # Security Policies
    ALLOW_NETWORK_ACCESS: bool = False
    ALLOW_FILESYSTEM_WRITE: bool = False
    ALLOWED_MODULES: list[str] = list(SAFE_STDLIB_MODULES)
    
    # Compiler Cache & Wheels Configuration
    CACHE_DIR: str = ".wasmbox_cache"
    ENABLE_COMPILER_CACHE: bool = True
    WHEELS_DIR: str = "wheels"
    ALLOWED_WHEELS: list[str] = []

    model_config = ConfigDict(case_sensitive=True)

settings = Settings()
