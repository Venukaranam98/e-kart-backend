"""Password hashing compatibility shim."""

from core.security import hash_password, pwd_context, verify_password

__all__ = ["hash_password", "pwd_context", "verify_password"]
