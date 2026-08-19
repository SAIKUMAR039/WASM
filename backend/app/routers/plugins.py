from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Plugin
from app.schemas import PluginCreate, PluginUpdate, PluginResponse

router = APIRouter(prefix="/plugins", tags=["Plugins"])

@router.get("", response_model=List[PluginResponse])
def list_plugins(tenant_id: str = "tenant_default", db: Session = Depends(get_db)):
    """Retrieve all saved Python plugins for a specific tenant."""
    return db.query(Plugin).filter(Plugin.tenant_id == tenant_id, Plugin.is_active == True).all()

@router.post("", response_model=PluginResponse, status_code=status.HTTP_201_CREATED)
def create_plugin(plugin_in: PluginCreate, db: Session = Depends(get_db)):
    """Create a new Python plugin."""
    db_plugin = Plugin(
        name=plugin_in.name,
        description=plugin_in.description,
        code=plugin_in.code,
        language=plugin_in.language,
        version=plugin_in.version,
        tenant_id=plugin_in.tenant_id
    )
    db.add(db_plugin)
    db.commit()
    db.refresh(db_plugin)
    return db_plugin

@router.get("/{plugin_id}", response_model=PluginResponse)
def get_plugin(plugin_id: str, db: Session = Depends(get_db)):
    """Get a specific plugin by ID."""
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin

@router.put("/{plugin_id}", response_model=PluginResponse)
def update_plugin(plugin_id: str, plugin_in: PluginUpdate, db: Session = Depends(get_db)):
    """Update an existing plugin's code or metadata."""
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    update_data = plugin_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plugin, field, value)
        
    db.commit()
    db.refresh(plugin)
    return plugin

@router.delete("/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plugin(plugin_id: str, db: Session = Depends(get_db)):
    """Soft delete a plugin by ID."""
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    plugin.is_active = False
    db.commit()
    return None
