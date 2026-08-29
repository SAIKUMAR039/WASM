import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.schemas import PluginCreate, PluginUpdate, PluginResponse
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/plugins", tags=["Plugins"])

_memory_plugins = {}

@router.get("", response_model=List[PluginResponse])
def list_plugins(tenant_id: Optional[str] = None, user=Depends(get_current_user), db=Depends(get_db)):
    """Retrieve all active Python plugins for tenant from MongoDB. Accessible to Admin, Developer, Viewer."""
    active_tenant = tenant_id or user.get("tenant_id", "tenant_default")
    if db is not None:
        docs = list(db["plugins"].find({"tenant_id": active_tenant, "is_active": True}))
        for d in docs:
            d["id"] = d.get("_id", d.get("id"))
        return docs
    
    return [p for p in _memory_plugins.values() if p["tenant_id"] == active_tenant and p["is_active"]]

@router.post("", response_model=PluginResponse, status_code=status.HTTP_201_CREATED)
def create_plugin(plugin_in: PluginCreate, user=Depends(require_roles(["Admin", "Developer"])), db=Depends(get_db)):
    """Create a new Python plugin document. Restricted to Admin and Developer."""
    plugin_id = str(uuid.uuid4())
    now = datetime.utcnow()
    active_tenant = user.get("tenant_id", plugin_in.tenant_id or "tenant_default")
    
    doc = {
        "_id": plugin_id,
        "id": plugin_id,
        "name": plugin_in.name,
        "description": plugin_in.description,
        "code": plugin_in.code,
        "language": plugin_in.language,
        "version": plugin_in.version,
        "tenant_id": active_tenant,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    if db is not None:
        db["plugins"].insert_one(doc)
    else:
        _memory_plugins[plugin_id] = doc

    return doc

@router.get("/{plugin_id}", response_model=PluginResponse)
def get_plugin(plugin_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    """Fetch specific plugin document by ID."""
    active_tenant = user.get("tenant_id", "tenant_default")
    if db is not None:
        plugin = db["plugins"].find_one({"_id": plugin_id, "tenant_id": active_tenant, "is_active": True})
        if not plugin:
            # Check without tenant constraint for backward compatibility
            plugin = db["plugins"].find_one({"_id": plugin_id, "is_active": True})
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")
        plugin["id"] = plugin.get("_id", plugin_id)
        return plugin

    if plugin_id not in _memory_plugins or not _memory_plugins[plugin_id]["is_active"]:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return _memory_plugins[plugin_id]

@router.put("/{plugin_id}", response_model=PluginResponse)
def update_plugin(plugin_id: str, plugin_in: PluginUpdate, user=Depends(require_roles(["Admin", "Developer"])), db=Depends(get_db)):
    """Update plugin document in MongoDB. Restricted to Admin and Developer."""
    update_data = plugin_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    if db is not None:
        res = db["plugins"].find_one_and_update(
            {"_id": plugin_id},
            {"$set": update_data},
            return_document=True
        )
        if not res:
            raise HTTPException(status_code=404, detail="Plugin not found")
        res["id"] = res.get("_id", plugin_id)
        return res

    if plugin_id not in _memory_plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    _memory_plugins[plugin_id].update(update_data)
    return _memory_plugins[plugin_id]

@router.delete("/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plugin(plugin_id: str, user=Depends(require_roles(["Admin", "Developer"])), db=Depends(get_db)):
    """Soft delete plugin document in MongoDB. Restricted to Admin and Developer."""
    if db is not None:
        res = db["plugins"].update_one({"_id": plugin_id}, {"$set": {"is_active": False}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Plugin not found")
        return None

    if plugin_id in _memory_plugins:
        _memory_plugins[plugin_id]["is_active"] = False
    return None
