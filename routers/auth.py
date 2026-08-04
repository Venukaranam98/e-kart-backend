"""Authentication and user profile router endpoints."""

import logging
from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from db.session import get_db
from dependencies.auth import (
    get_current_admin,
    get_current_user,
    oauth2_scheme,
)
from models import PasswordResetToken, User
from redis_client import redis_client
from schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserSchema,
)
from tasks.email_tasks import (
    send_login_alert,
    send_password_changed,
    send_password_reset,
    send_welcome_email,
)
from utils.token import (
    generate_reset_token,
    get_token_expiry,
    is_token_expired,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
def register(
    user: UserSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Register a new user account."""
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Email already registered"},
        )

    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        created_at_str = (
            new_user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if getattr(new_user, "created_at", None)
            else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        )
        background_tasks.add_task(
            send_welcome_email,
            new_user.id,
            new_user.email,
            new_user.username,
            created_at_str,
        )
    except Exception as e:
        logger.warning(f"[Register Email Queue Warning]: {e}")

    access_token = create_access_token(data={"sub": new_user.email})

    return {
        "success": True,
        "message": "Registration Successful",
        "data": {"access_token": access_token, "token_type": "bearer"},
    }


@router.post("/login", tags=["Authentication"])
@router.post("/auth/login", tags=["Authentication"])
def login(
    req: Request,
    background_tasks: BackgroundTasks,
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Authenticate user with credentials and return JWT token."""
    attempts_key = f"login_attempts:{request.username}"
    attempts = redis_client.get(attempts_key)

    if attempts and int(attempts) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "message": "Too many failed login attempts. Try again in 15 minutes.",
            },
        )

    existing_user = db.query(User).filter(User.email == request.username).first()
    if not existing_user:
        redis_client.incr(attempts_key)
        redis_client.expire(attempts_key, 900)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "User not found"},
        )

    password_valid = verify_password(request.password, existing_user.password)
    if not password_valid:
        redis_client.incr(attempts_key)
        redis_client.expire(attempts_key, 900)

        curr_attempts = redis_client.get(attempts_key)
        remaining = 5 - (int(curr_attempts) if curr_attempts else 1)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": f"Invalid password. {remaining} attempts remaining.",
            },
        )

    redis_client.delete(attempts_key)

    try:
        user_agent = req.headers.get("user-agent", "Unknown Client")
        browser = "Web Browser"
        device = "Desktop/Mobile"
        if "Chrome" in user_agent:
            browser = "Chrome Browser"
        elif "Firefox" in user_agent:
            browser = "Firefox Browser"
        elif "Safari" in user_agent:
            browser = "Safari Browser"

        login_time_str = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
        background_tasks.add_task(
            send_login_alert,
            existing_user.id,
            existing_user.email,
            existing_user.username,
            browser,
            device,
            login_time_str,
        )
    except Exception as e:
        logger.warning(f"[Login Alert Queue Warning]: {e}")

    access_token = create_access_token(data={"sub": existing_user.email})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/forgot-password", tags=["Authentication"])
def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Request a password reset link for registered email."""
    logger.info(
        f"[Forgot Password Request Received] Processing request for email: {payload.email}"
    )
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        logger.info(f"[User Found] User ID: {user.id} | Email: {user.email}")
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
        ).update({"used": True})

        token = generate_reset_token()
        expires_at = get_token_expiry(minutes=15)

        reset_token_entry = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            used=False,
        )
        db.add(reset_token_entry)
        db.commit()
        logger.info(
            f"[Token Generated & Stored] User ID: {user.id} | Token generated, expires at: {expires_at}"
        )

        try:
            background_tasks.add_task(
                send_password_reset,
                user.id,
                user.email,
                user.username,
                token,
                15,
            )
        except Exception as e:
            logger.error(
                f"[Forgot Password Email Queue Failed] Failed to queue send_password_reset task for email {user.email}: {e}",
                exc_info=True,
            )
    else:
        logger.info(
            f"[Forgot Password Request] No user account found with email: {payload.email}"
        )

    return {
        "success": True,
        "message": "If an account with that email exists, a password reset link has been sent to your inbox.",
    }


@router.post("/auth/reset-password", tags=["Authentication"])
def reset_password(
    payload: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reset user password using reset token."""
    token_record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == payload.token,
            PasswordResetToken.used == False,
        )
        .first()
    )

    if not token_record or is_token_expired(token_record.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Invalid or expired password reset token. Please request a new link.",
            },
        )

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "User not found."},
        )

    user.password = hash_password(payload.new_password)
    token_record.used = True
    db.commit()

    try:
        change_time_str = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
        background_tasks.add_task(
            send_password_changed,
            user.id,
            user.email,
            user.username,
            change_time_str,
        )
    except Exception as e:
        logger.warning(f"[Password Changed Email Queue Warning]: {e}")

    return {
        "success": True,
        "message": "Your password has been successfully reset. You can now log in with your new password.",
    }


@router.post("/auth/logout", tags=["Authentication"])
def logout() -> dict[str, Any]:
    """User logout endpoint."""
    return {"success": True, "message": "Logged out successfully"}


@router.get("/profile", tags=["Authentication"])
@router.get("/auth/me", tags=["Authentication"])
def get_profile(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Fetch current user profile details."""
    return {
        "success": True,
        "message": "Profile fetched successfully",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
        },
    }


@router.get("/admin/profile", tags=["Authentication"])
def admin_profile(
    current_admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Fetch current admin profile details."""
    return {
        "success": True,
        "message": "Admin authorized successfully",
        "data": {
            "id": current_admin.id,
            "username": current_admin.username,
            "email": current_admin.email,
            "is_admin": current_admin.is_admin,
        },
    }


@router.get("/test-token")
def test_token() -> dict[str, Any]:
    """Utility endpoint to test secret key initialization."""
    from core.security import SECRET_KEY

    return {"secret_key": SECRET_KEY}


# Compatibility re-exports for dependency consumers importing from routers.auth
__all__ = [
    "get_current_admin",
    "get_current_user",
    "oauth2_scheme",
    "router",
]
