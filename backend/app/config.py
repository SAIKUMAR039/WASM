from pydantic_settings import BaseSettings

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
    ALLOWED_MODULES: list[str] = ["math", "json", "re", "datetime", "random", "hashlib", "collections", "itertools", "functools", "base64", "zlib"]
    
    class Config:
        case_sensitive = True

settings = Settings()
