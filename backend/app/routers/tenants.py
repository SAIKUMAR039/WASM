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

import hashlib
import secrets
from datetime import timedelta
from app.schemas import ApiKeyCreate, ApiKeyResponse

_memory_api_keys = {}

def _generate_api_key():
    entropy = secrets.token_urlsafe(32)
    raw_key = f"wsm_live_{entropy}"
    prefix = raw_key[:14] + "..."
    hashed = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, prefix, hashed

@router.post("/{tenant_id}/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(tenant_id: str, key_in: ApiKeyCreate, db=Depends(get_db)):
    """Generate a high-entropy API key for automated tenant access and store its SHA-256 hash."""
    raw_key, prefix, hashed = _generate_api_key()
    key_id = str(uuid.uuid4())
    now = datetime.utcnow()
    expires_at = now + timedelta(days=key_in.expires_days or 90)
    
    doc = {
        "_id": key_id,
        "id": key_id,
        "tenant_id": tenant_id,
        "user_id": None,
        "name": key_in.name,
        "key_prefix": prefix,
        "hashed_key": hashed,
        "role": key_in.role if key_in.role in ["Admin", "Developer", "Viewer"] else "Developer",
        "is_active": True,
        "created_at": now,
        "expires_at": expires_at,
        "last_used_at": None
    }
    
    if db is not None:
        db["api_keys"].insert_one(doc)
    else:
        _memory_api_keys[key_id] = doc
        
    doc["raw_key"] = raw_key
    return doc

@router.get("/{tenant_id}/api-keys", response_model=List[ApiKeyResponse])
def list_api_keys(tenant_id: str, db=Depends(get_db)):
    """List all active API keys for a tenant (returns key prefix only)."""
    if db is not None:
        docs = list(db["api_keys"].find({"tenant_id": tenant_id, "is_active": True}))
        for d in docs:
            d["id"] = d.get("_id", d.get("id"))
        return docs
    return [k for k in _memory_api_keys.values() if k["tenant_id"] == tenant_id and k["is_active"]]

@router.delete("/{tenant_id}/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(tenant_id: str, key_id: str, db=Depends(get_db)):
    """Revoke an API key."""
    if db is not None:
        res = db["api_keys"].update_one({"_id": key_id, "tenant_id": tenant_id}, {"$set": {"is_active": False}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="API key not found")
        return None
        
    if key_id in _memory_api_keys and _memory_api_keys[key_id]["tenant_id"] == tenant_id:
        _memory_api_keys[key_id]["is_active"] = False
        return None
    raise HTTPException(status_code=404, detail="API key not found")
