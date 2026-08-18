import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

def generate_id():
    return str(uuid.uuid4())

class PluginDocument(BaseModel):
    id: str = Field(default_factory=generate_id, alias="_id")
    name: str
    description: Optional[str] = None
    code: str
    language: str = "python"
    version: str = "1.0.0"
    tenant_id: str = "tenant_default"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class ExecutionDocument(BaseModel):
    id: str = Field(default_factory=generate_id, alias="_id")
    plugin_id: Optional[str] = None
    tenant_id: str = "tenant_default"
    status: str  # SUCCESS, ERROR, TIMEOUT, SECURITY_VIOLATION
    input_data: Optional[Any] = None
    output_result: Optional[Any] = None
    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    execution_time_sec: float = 0.0
    memory_used_mb: float = 0.0
    executed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class SandboxPolicyDocument(BaseModel):
    id: str = Field(default_factory=generate_id, alias="_id")
    tenant_id: str = "tenant_default"
    memory_limit_mb: int = 128
    timeout_sec: float = 5.0
    allow_network: bool = False
    allow_filesystem: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class SystemLogDocument(BaseModel):
    id: str = Field(default_factory=generate_id, alias="_id")
    tenant_id: str = "tenant_default"
    level: str = "INFO"
    event: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class UserDocument(BaseModel):
    id: str = Field(default_factory=generate_id, alias="_id")
    username: str
    email: str
    hashed_password: str
    role: str = "Developer"  # Admin, Developer, Viewer
    tenant_id: str = "tenant_default"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class TenantDocument(BaseModel):
    id: str = Field(default_factory=generate_id, alias="_id")
    name: str
    slug: str
    plan: str = "Free"  # Free, Pro, Enterprise
    owner_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class ApiKeyDocument(BaseModel):
    id: str = Field(default_factory=generate_id, alias="_id")
    tenant_id: str = "tenant_default"
    user_id: Optional[str] = None
    name: str
    key_prefix: str
    hashed_key: str
    role: str = "Developer"  # Admin, Developer, Viewer
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
