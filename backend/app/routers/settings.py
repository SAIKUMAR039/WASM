from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SandboxPolicy
from app.schemas import SandboxPolicySchema

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=SandboxPolicySchema)
def get_sandbox_policy(tenant_id: str = "tenant_default", db: Session = Depends(get_db)):
    """Fetch current sandbox security policy for tenant."""
    policy = db.query(SandboxPolicy).filter(SandboxPolicy.tenant_id == tenant_id).first()
    if not policy:
        # Default policy
        policy = SandboxPolicy(tenant_id=tenant_id, memory_limit_mb=128, timeout_sec=5.0, allow_network=False, allow_filesystem=False)
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy

@router.put("", response_model=SandboxPolicySchema)
def update_sandbox_policy(policy_in: SandboxPolicySchema, db: Session = Depends(get_db)):
    """Update sandbox resource limits and security constraints."""
    policy = db.query(SandboxPolicy).filter(SandboxPolicy.tenant_id == policy_in.tenant_id).first()
    if not policy:
        policy = SandboxPolicy(tenant_id=policy_in.tenant_id)
        db.add(policy)
        
    policy.memory_limit_mb = policy_in.memory_limit_mb
    policy.timeout_sec = policy_in.timeout_sec
    policy.allow_network = policy_in.allow_network
    policy.allow_filesystem = policy_in.allow_filesystem
    
    db.commit()
    db.refresh(policy)
    return policy
