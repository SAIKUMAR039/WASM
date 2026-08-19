import hmac
import hashlib
import secrets

def hash_password(password: str) -> str:
    """Generate a PBKDF2-HMAC-SHA256 salted password hash with 100,000 iterations."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against the stored salted hash."""
    try:
        salt, stored_hash = hashed_password.split(":")
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return hmac.compare_digest(key.hex(), stored_hash)
    except Exception:
        return False
