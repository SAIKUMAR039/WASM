from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class PluginBase(BaseModel):
    name: str = Field(..., example="JSON Processor")
    description: Optional[str] = Field(None, example="Transforms input payload into uppercased keys")
    code: str = Field(..., example="def process(data):\n    return {'result': data.upper()}")
    language: str = "python"
    version: str = "1.0.0"
    category: Optional[str] = "general"
    tags: list[str] = []
    tenant_id: str = "tenant_default"

class PluginCreate(PluginBase):
    pass

class PluginUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None

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
    env_vars: Optional[dict[str, str]] = None
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
    peak_memory_mb: Optional[float] = None
    memory_leak_warning: Optional[bool] = False
    fuel_consumed: Optional[int] = None
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

class TenantQuotaSchema(BaseModel):
    tenant_id: str = "tenant_default"
    tier: str = "pro"
    max_daily_executions: int = 1000
    max_memory_limit_mb: int = 256
    executions_today: int = 0
    remaining_today: int = 1000

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
    env_vars: Optional[dict[str, str]] = None
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

class BenchmarkRequest(BaseModel):
    plugin_id: Optional[str] = None
    code: Optional[str] = None
    input_data: Optional[Any] = "HELLO WORLD"
    tenant_id: str = "tenant_default"
    iterations: int = Field(default=10, ge=2, le=100)

class BenchmarkResponse(BaseModel):
    iterations: int
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    avg_memory_mb: float
    total_fuel_consumed: int
    success_rate_pct: float
    raw_latencies_ms: list[float] = []

class CodeValidationRequest(BaseModel):
    code: str
    custom_allowed_modules: Optional[list[str]] = None

class CodeValidationResponse(BaseModel):
    is_valid: bool
    errors: list[str] = []
    line_numbers: list[int] = []

class BytecodeSectionInfo(BaseModel):
    name: str
    size_bytes: int
    preview: Optional[str] = None

class BytecodeInspectionRequest(BaseModel):
    code: str

class BytecodeInspectionResponse(BaseModel):
    cache_key: str
    wasm_size_bytes: int
    header_magic: str
    header_version: int
    fuel_estimate: int
    sections: list[BytecodeSectionInfo] = []

class JobSubmitRequest(BaseModel):
    plugin_id: Optional[str] = None
    code: Optional[str] = None
    input_data: Optional[Any] = "HELLO WORLD"
    env_vars: Optional[dict[str, str]] = None
    tenant_id: str = "tenant_default"
    callback_url: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    tenant_id: str = "tenant_default"
    status: str  # PENDING, RUNNING, COMPLETED, FAILED, SECURITY_VIOLATION
    output_result: Optional[Any] = None
    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    execution_time_sec: Optional[float] = None
    memory_used_mb: Optional[float] = None
    error: Optional[str] = None
    submitted_at: datetime
    completed_at: Optional[datetime] = None
    callback_url: Optional[str] = None






