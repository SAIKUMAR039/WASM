import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from app.database import get_db
from app.schemas import SandboxPolicySchema, TenantQuotaSchema

router = APIRouter(prefix="/settings", tags=["Settings"])

_memory_policy = {
    "tenant_id": "tenant_default",
    "memory_limit_mb": 128,
    "timeout_sec": 5.0,
    "allow_network": False,
    "allow_filesystem": False
}

@router.get("", response_model=SandboxPolicySchema)
def get_sandbox_policy(tenant_id: str = "tenant_default", db=Depends(get_db)):
    """Fetch current sandbox security policy document from MongoDB."""
    if db is not None:
        policy = db["sandbox_policies"].find_one({"tenant_id": tenant_id})
        if not policy:
            policy = {
                "_id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "memory_limit_mb": 128,
                "timeout_sec": 5.0,
                "allow_network": False,
                "allow_filesystem": False,
                "updated_at": datetime.utcnow()
            }
            db["sandbox_policies"].insert_one(policy)
        return policy

    return _memory_policy

@router.put("", response_model=SandboxPolicySchema)
def update_sandbox_policy(policy_in: SandboxPolicySchema, db=Depends(get_db)):
    """Update sandbox policy document in MongoDB."""
    policy_data = policy_in.model_dump()
    policy_data["updated_at"] = datetime.utcnow()

    if db is not None:
        db["sandbox_policies"].update_one(
            {"tenant_id": policy_in.tenant_id},
            {"$set": policy_data},
            upsert=True
        )
        return policy_data

    _memory_policy.update(policy_data)
    return _memory_policy


_memory_quota = {
    "tenant_id": "tenant_default",
    "tier": "pro",
    "max_daily_executions": 1000,
    "max_memory_limit_mb": 256,
    "executions_today": 24,
    "remaining_today": 976
}

@router.get("/quota", response_model=TenantQuotaSchema)
def get_tenant_quota(tenant_id: str = "tenant_default", db=Depends(get_db)):
    """Fetch current tenant tier quota and daily execution usage."""
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    if db is not None:
        doc = db["tenant_quotas"].find_one({"tenant_id": tenant_id})
        if not doc:
            doc = {
                "_id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "tier": "pro",
                "max_daily_executions": 1000,
                "max_memory_limit_mb": 256,
                "executions_today": 0,
                "last_reset_date": today_str,
                "updated_at": datetime.utcnow()
            }
            db["tenant_quotas"].insert_one(doc)

        execs_today = doc.get("executions_today", 0)
        max_daily = doc.get("max_daily_executions", 1000)
        return {
            "tenant_id": tenant_id,
            "tier": doc.get("tier", "pro"),
            "max_daily_executions": max_daily,
            "max_memory_limit_mb": doc.get("max_memory_limit_mb", 256),
            "executions_today": execs_today,
            "remaining_today": max(0, max_daily - execs_today)
        }

    return _memory_quota

