import secrets
from datetime import datetime, timedelta

def generate_reset_token() -> str:
    """Generate a cryptographically secure random password reset token."""
    return secrets.token_urlsafe(32)

def get_token_expiry(minutes: int = 15) -> datetime:
    """Calculate token expiration datetime."""
    return datetime.utcnow() + timedelta(minutes=minutes)

def is_token_expired(expires_at: datetime) -> bool:
    """Check if token expiration date has passed."""
    if not expires_at:
        return True
    return datetime.utcnow() > expires_at
