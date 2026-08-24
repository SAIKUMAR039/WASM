import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.schemas import UserRegister, TokenResponse, UserResponse
from app.auth import hash_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

_memory_users = {}
_memory_tenants = {}

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserRegister, db=Depends(get_db)):
    """Register a new user, create an organization tenant, and issue a JWT access token."""
    now = datetime.utcnow()
    user_id = str(uuid.uuid4())
    tenant_id = f"tenant_{user_in.username.lower()}"
    
    # Check duplicate in MongoDB
    if db is not None:
        existing = db["users"].find_one({
            "$or": [{"username": user_in.username}, {"email": user_in.email}]
        })
        if existing:
            raise HTTPException(status_code=400, detail="Username or email is already registered")
        
        # Check / provision tenant
        tenant_name = user_in.organization_name or f"{user_in.username}'s Org"
        tenant_doc = db["tenants"].find_one({"_id": tenant_id})
        if not tenant_doc:
            tenant_doc = {
                "_id": tenant_id,
                "id": tenant_id,
                "name": tenant_name,
                "slug": user_in.username.lower(),
                "plan": "Free",
                "owner_id": user_id,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
            db["tenants"].insert_one(tenant_doc)
            
        # Create user
        user_doc = {
            "_id": user_id,
            "id": user_id,
            "username": user_in.username,
            "email": user_in.email,
            "hashed_password": hash_password(user_in.password),
            "role": user_in.role if user_in.role in ["Admin", "Developer", "Viewer"] else "Developer",
            "tenant_id": tenant_id,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        db["users"].insert_one(user_doc)
    else:
        # Fallback memory store
        for u in _memory_users.values():
            if u["username"] == user_in.username or u["email"] == user_in.email:
                raise HTTPException(status_code=400, detail="Username or email is already registered")
        
        tenant_name = user_in.organization_name or f"{user_in.username}'s Org"
        _memory_tenants[tenant_id] = {
            "_id": tenant_id,
            "id": tenant_id,
            "name": tenant_name,
            "slug": user_in.username.lower(),
            "plan": "Free",
            "owner_id": user_id,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        user_doc = {
            "_id": user_id,
            "id": user_id,
            "username": user_in.username,
            "email": user_in.email,
            "hashed_password": hash_password(user_in.password),
            "role": user_in.role if user_in.role in ["Admin", "Developer", "Viewer"] else "Developer",
            "tenant_id": tenant_id,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        _memory_users[user_id] = user_doc

    token = create_access_token({
        "sub": user_id,
        "username": user_doc["username"],
        "email": user_doc["email"],
        "role": user_doc["role"],
        "tenant_id": user_doc["tenant_id"]
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_doc
    }

from app.schemas import UserLogin
from app.auth import verify_password

@router.post("/login", response_model=TokenResponse)
def login_user(creds: UserLogin, db=Depends(get_db)):
    """Authenticate user with username or email and return JWT access token."""
    user = None
    if db is not None:
        user = db["users"].find_one({
            "$or": [{"username": creds.username}, {"email": creds.username}],
            "is_active": True
        })
    else:
        for u in _memory_users.values():
            if (u["username"] == creds.username or u["email"] == creds.username) and u["is_active"]:
                user = u
                break

    if not user or not verify_password(creds.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )

    user["id"] = user.get("_id", user.get("id"))
    token = create_access_token({
        "sub": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "tenant_id": user["tenant_id"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

@router.get("/me")
def get_current_user_profile(
    bearer: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db=Depends(get_db)
):
    """Retrieve profile and organization metadata for the currently authenticated user."""
    if not bearer or not bearer.credentials:
        raise HTTPException(status_code=401, detail="Authentication token required")

    payload = decode_access_token(bearer.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    user = None
    if db is not None:
        user = db["users"].find_one({"_id": user_id, "is_active": True})
        if user:
            user["id"] = user.get("_id", user_id)
            user.pop("hashed_password", None)
            tenant = db["tenants"].find_one({"_id": user.get("tenant_id")})
            user["tenant_name"] = tenant.get("name") if tenant else "Default Organization"
            return user

    if user_id in _memory_users and _memory_users[user_id]["is_active"]:
        user = dict(_memory_users[user_id])
        user.pop("hashed_password", None)
        tenant = _memory_tenants.get(user.get("tenant_id"))
        user["tenant_name"] = tenant.get("name") if tenant else "Default Organization"
        return user

    # Construct from token payload
    return {
        "id": user_id,
        "username": payload.get("username", "user"),
        "email": payload.get("email", ""),
        "role": payload.get("role", "Developer"),
        "tenant_id": payload.get("tenant_id", "tenant_default"),
        "tenant_name": "Default Organization",
        "is_active": True
    }
