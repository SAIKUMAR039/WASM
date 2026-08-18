import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(Text, nullable=False)
    language = Column(String(20), default="python")
    version = Column(String(20), default="1.0.0")
    tenant_id = Column(String(50), default="tenant_default")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Execution(Base):
    __tablename__ = "executions"

    id = Column(String, primary_key=True, default=generate_uuid)
    plugin_id = Column(String, ForeignKey("plugins.id"), nullable=True)
    tenant_id = Column(String(50), default="tenant_default")
    status = Column(String(20), nullable=False)  # SUCCESS, ERROR, TIMEOUT, SECURITY_VIOLATION
    input_data = Column(Text, nullable=True)
    output_result = Column(Text, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    execution_time_sec = Column(Float, default=0.0)
    memory_used_mb = Column(Float, default=0.0)
    executed_at = Column(DateTime, default=datetime.utcnow)

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), default="tenant_default")
    level = Column(String(10), default="INFO")
    event = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SandboxPolicy(Base):
    __tablename__ = "sandbox_policies"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), default="tenant_default", unique=True)
    memory_limit_mb = Column(Integer, default=128)
    timeout_sec = Column(Float, default=5.0)
    allow_network = Column(Boolean, default=False)
    allow_filesystem = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
