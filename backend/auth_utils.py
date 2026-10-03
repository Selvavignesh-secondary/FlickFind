import hashlib
import bcrypt


def _pre_hash_password(password: str) -> bytes:
    """SHA-256 pre-hash to avoid bcrypt's 72-byte input limit."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")

def hash_user_password(password: str) -> str:
    """Bcrypt hash with salting. Safe to store directly."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(_pre_hash_password(password), salt).decode("utf-8")

def verify_user_password(plain_password: str, hashed_password: str) -> bool:
    """Returns True if plain_password matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(_pre_hash_password(plain_password), hashed_password.encode("utf-8"))
    except Exception:
        return False