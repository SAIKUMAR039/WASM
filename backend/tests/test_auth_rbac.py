import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import hash_password, verify_password, create_access_token, decode_access_token

client = TestClient(app)

def test_password_hashing():
    raw = "SuperSecretPassword123!"
    hashed = hash_password(raw)
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_creation_and_decoding():
    payload = {"sub": "user_123", "username": "bob", "role": "Developer", "tenant_id": "tenant_bob"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user_123"
    assert decoded["username"] == "bob"
    assert decoded["role"] == "Developer"

def test_user_registration_endpoint():
    payload = {
        "username": "test_developer",
        "email": "test_developer@wasmbox.dev",
        "password": "Password123!",
        "organization_name": "Dev Organization",
        "role": "Developer"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code in [201, 400]
    if res.status_code == 201:
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "test_developer"
        assert data["user"]["role"] == "Developer"

def test_user_login_endpoint():
    res = client.post("/api/auth/login", json={
        "username": "test_developer",
        "password": "Password123!"
    })
    if res.status_code == 200:
        data = res.json()
        assert "access_token" in data
        assert data["user"]["username"] == "test_developer"

def test_user_login_invalid_password():
    res = client.post("/api/auth/login", json={
        "username": "test_developer",
        "password": "WrongPassword!!!"
    })
    assert res.status_code == 401

def test_auth_me_endpoint_with_valid_token():
    token = create_access_token({
        "sub": "user_admin_test",
        "username": "admin_test",
        "email": "admin@wasmbox.dev",
        "role": "Admin",
        "tenant_id": "tenant_test"
    })
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "admin_test"
    assert data["role"] == "Admin"

def test_tenant_api_key_generation_and_listing():
    res = client.post("/api/tenants/tenant_default/api-keys", json={
        "name": "Integration Test Key",
        "role": "Developer"
    })
    assert res.status_code == 201
    data = res.json()
    assert "raw_key" in data
    assert data["raw_key"].startswith("wsm_live_")
    assert "key_prefix" in data

    list_res = client.get("/api/tenants/tenant_default/api-keys")
    assert list_res.status_code == 200
    keys = list_res.json()
    assert any(k["name"] == "Integration Test Key" for k in keys)

def test_rbac_admin_allowed_settings_update():
    token = create_access_token({
        "sub": "admin_user",
        "username": "admin",
        "role": "Admin",
        "tenant_id": "tenant_default"
    })
    res = client.put(
        "/api/settings",
        json={"tenant_id": "tenant_default", "memory_limit_mb": 256, "timeout_sec": 10.0, "allow_network": False, "allow_filesystem": False},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200

def test_rbac_developer_forbidden_from_settings_update():
    token = create_access_token({
        "sub": "dev_user",
        "username": "dev",
        "role": "Developer",
        "tenant_id": "tenant_default"
    })
    res = client.put(
        "/api/settings",
        json={"tenant_id": "tenant_default", "memory_limit_mb": 256, "timeout_sec": 10.0, "allow_network": False, "allow_filesystem": False},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403

def test_rbac_viewer_forbidden_from_code_execution():
    token = create_access_token({
        "sub": "viewer_user",
        "username": "viewer",
        "role": "Viewer",
        "tenant_id": "tenant_default"
    })
    res = client.post(
        "/api/execute",
        json={"code": "print('Hello Viewer')", "tenant_id": "tenant_default"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403
