import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.schemas import TenantCreate, TenantResponse

router = APIRouter(prefix="/tenants", tags=["Multi-Tenancy & Organizations"])

_memory_tenants = {
    "tenant_default": {
        "_id": "tenant_default",
        "id": "tenant_default",
        "name": "Default Organization",
        "slug": "default-org",
        "plan": "Enterprise",
        "owner_id": "user_default",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
}

@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(tenant_in: TenantCreate, db=Depends(get_db)):
    """Create a new tenant organization in MongoDB."""
    tenant_id = f"tenant_{str(uuid.uuid4())[:8]}"
    slug = tenant_in.name.lower().replace(" ", "-")
    now = datetime.utcnow()
    
    doc = {
        "_id": tenant_id,
        "id": tenant_id,
        "name": tenant_in.name,
        "slug": slug,
        "plan": tenant_in.plan or "Free",
        "owner_id": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    if db is not None:
        db["tenants"].insert_one(doc)
    else:
        _memory_tenants[tenant_id] = doc
        
    return doc

@router.get("", response_model=List[TenantResponse])
def list_tenants(db=Depends(get_db)):
    """List all active organization tenants."""
    if db is not None:
        docs = list(db["tenants"].find({"is_active": True}))
        for d in docs:
            d["id"] = d.get("_id", d.get("id"))
        return docs
    return list(_memory_tenants.values())

@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: str, db=Depends(get_db)):
    """Retrieve tenant details by ID."""
    if db is not None:
        doc = db["tenants"].find_one({"_id": tenant_id, "is_active": True})
        if not doc:
            raise HTTPException(status_code=404, detail="Tenant organization not found")
        doc["id"] = doc.get("_id", tenant_id)
        return doc

    if tenant_id in _memory_tenants and _memory_tenants[tenant_id]["is_active"]:
        return _memory_tenants[tenant_id]
    raise HTTPException(status_code=404, detail="Tenant organization not found")
