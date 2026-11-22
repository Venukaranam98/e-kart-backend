"""FastAPI authentication and current user/admin dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.security import verify_access_token
from db.session import get_db
from models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
oauth2_optional_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Validate access token and return the authenticated User instance."""
    email = verify_access_token(token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "message": "Invalid Token"},
        )
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "message": "User not found"},
        )
    return user


def get_optional_current_user(
    token: str | None = Depends(oauth2_optional_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Validate access token if present and return the User instance, or None if anonymous."""
    if not token:
        return None
    email = verify_access_token(token)
    if email is None:
        return None
    return db.query(User).filter(User.email == email).first()


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Validate that the current user possesses administrative privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "Not authorized"},
        )
    return current_user
