from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

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

class StreamExecutionRequest(BaseModel):
    plugin_id: Optional[str] = None
    code: Optional[str] = None
    input_data: Optional[Any] = "HELLO WORLD"
    tenant_id: str = "tenant_default"

class StreamChunkEvent(BaseModel):
    type: str  # "stdout", "stderr", "status", "result", "error"
    data: Optional[str] = None
    status: Optional[str] = None
    id: Optional[str] = None

class ExecutionTrendPoint(BaseModel):
    id: str
    timestamp: str
    execution_time_sec: float
    memory_used_mb: float
    status: str
    plugin_id: Optional[str] = None

class TrendSummaryResponse(BaseModel):
    tenant_id: str
    count: int
    p50_latency_sec: float
    p95_latency_sec: float
    p99_latency_sec: float
    avg_memory_mb: float
    trends: list[ExecutionTrendPoint] = []


