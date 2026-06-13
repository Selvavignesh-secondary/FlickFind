# auth_utils.py - Native, High-Performance Hashing Engine
import hashlib
import bcrypt

def _pre_hash_password(password: str) -> bytes:
    """
    Deterministically converts any plain text passphrase into a 64-character hex string,
    then encodes it to raw bytes. This ensures absolute safety against size ceilings.
    """
    hex_string = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hex_string.encode("utf-8")

def hash_user_password(password: str) -> str:
    """Native encryption pass: Automatically handles salting and processing safely."""
    pre_hashed_bytes = _pre_hash_password(password)
    
    # Generate a secure unique random salt factor
    salt = bcrypt.gensalt()
    
    # Hash the bytes and decode the resulting binary back to a clean string for storage
    hashed_bytes = bcrypt.hashpw(pre_hashed_bytes, salt)
    return hashed_bytes.decode("utf-8")

def verify_user_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies an incoming login password against the database binary string string signature."""
    try:
        pre_hashed_bytes = _pre_hash_password(plain_password)
        stored_hash_bytes = hashed_password.encode("utf-8")
        
        # Returns a direct boolean comparison
        return bcrypt.checkpw(pre_hashed_bytes, stored_hash_bytes)
    except Exception:
        return False