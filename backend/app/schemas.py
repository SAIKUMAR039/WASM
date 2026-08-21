from typing import Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class UserRole(str, Enum):
    ADMIN = "Admin"
    DEVELOPER = "Developer"
    VIEWER = "Viewer"

class PluginBase(BaseModel):
    name: str = Field(..., example="JSON Processor")
    description: Optional[str] = Field(None, example="Transforms input payload into uppercased keys")
    code: str = Field(..., example="def process(data):\n    return {'result': data.upper()}")
    language: str = "python"
    version: str = "1.0.0"
    tenant_id: str = "tenant_default"

class PluginCreate(PluginBase):
    pass

class PluginUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    version: Optional[str] = None

class PluginResponse(PluginBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExecutionRequest(BaseModel):
    plugin_id: Optional[str] = None
    code: Optional[str] = None
    input_data: Optional[Any] = "HELLO WORLD"
    tenant_id: str = "tenant_default"

class ExecutionResponse(BaseModel):
    id: str
    plugin_id: Optional[str] = None
    status: str  # SUCCESS, ERROR, TIMEOUT, SECURITY_VIOLATION
    output_result: Optional[Any] = None
    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    execution_time_sec: float
    memory_used_mb: float
    executed_at: datetime

    class Config:
        from_attributes = True

class SandboxPolicySchema(BaseModel):
    tenant_id: str = "tenant_default"
    memory_limit_mb: int = 128
    timeout_sec: float = 5.0
    allow_network: bool = False
    allow_filesystem: bool = False

    class Config:
        from_attributes = True

class SystemLogSchema(BaseModel):
    id: str
    tenant_id: str
    level: str
    event: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True

# --- User & Auth Schemas ---
class UserRegister(BaseModel):
    username: str = Field(..., example="alice")
    email: str = Field(..., example="alice@wasmbox.dev")
    password: str = Field(..., example="securePassword123")
    organization_name: Optional[str] = Field(None, example="Acme Corp")
    role: Optional[str] = Field("Developer", example="Developer")

class UserLogin(BaseModel):
    username: str = Field(..., example="alice")
    password: str = Field(..., example="securePassword123")

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    tenant_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Tenant & API Key Schemas ---
class TenantCreate(BaseModel):
    name: str = Field(..., example="Acme Corporation")
    plan: Optional[str] = Field("Free", example="Pro")

class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    owner_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApiKeyCreate(BaseModel):
    name: str = Field(..., example="CI/CD Deployment Key")
    role: Optional[str] = Field("Developer", example="Developer")
    expires_days: Optional[int] = Field(90, example=90)

class ApiKeyResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    key_prefix: str
    role: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    raw_key: Optional[str] = None

    class Config:
        from_attributes = True
