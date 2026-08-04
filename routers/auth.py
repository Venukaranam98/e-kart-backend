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
    summary="Register New User",
    description="Create a new user account with username, email, and password. Asynchronously queues a welcome email.",
    response_description="JWT token object and success confirmation",
    tags=["Authentication"],
    responses={
        201: {
            "description": "User successfully created.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Registration Successful",
                        "data": {
                            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "token_type": "bearer",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Email already registered.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "success": False,
                            "message": "Email already registered",
                        }
                    }
                }
            },
        },
        422: {"description": "Validation Error (missing or invalid payload)"},
    },
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


@router.post(
    "/login",
    summary="Authenticate User (Login)",
    description="Authenticate registered user using email (username) and password. Protected by Redis rate limiting (max 5 failed attempts per 15 mins). Queues login alert notification.",
    response_description="OAuth2 Bearer JWT Access Token payload",
    tags=["Authentication"],
    responses={
        200: {
            "description": "Authentication successful.",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: {
            "description": "Invalid password credentials.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "success": False,
                            "message": "Invalid password. 4 attempts remaining.",
                        }
                    }
                }
            },
        },
        404: {
            "description": "User account not found.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {"success": False, "message": "User not found"}
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded (too many login attempts).",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "success": False,
                            "message": "Too many failed login attempts. Try again in 15 minutes.",
                        }
                    }
                }
            },
        },
    },
)
@router.post("/auth/login", tags=["Authentication"], include_in_schema=False)
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


@router.post(
    "/auth/forgot-password",
    summary="Request Password Reset Link",
    description="Generate a secure single-use 15-minute reset token and dispatch an email reset link to user's registered inbox.",
    response_description="Confirmation notice",
    tags=["Authentication"],
    responses={
        200: {
            "description": "Password reset email queued if account exists.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "If an account with that email exists, a password reset link has been sent to your inbox.",
                    }
                }
            },
        }
    },
)
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


@router.post(
    "/auth/reset-password",
    summary="Reset User Password",
    description="Update account password using a valid unexpired password reset token received via email.",
    response_description="Password reset confirmation message",
    tags=["Authentication"],
    responses={
        200: {
            "description": "Password reset successful.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Your password has been successfully reset. You can now log in with your new password.",
                    }
                }
            },
        },
        400: {
            "description": "Invalid or expired reset token.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "success": False,
                            "message": "Invalid or expired password reset token. Please request a new link.",
                        }
                    }
                }
            },
        },
    },
)
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


@router.post(
    "/auth/logout",
    summary="User Logout",
    description="Logout user session.",
    response_description="Logout status confirmation",
    tags=["Authentication"],
)
def logout() -> dict[str, Any]:
    """User logout endpoint."""
    return {"success": True, "message": "Logged out successfully"}


@router.get(
    "/profile",
    summary="Get Current User Profile",
    description="Retrieve account details for authenticated user using Bearer JWT token.",
    response_description="Authenticated user profile object",
    tags=["Authentication"],
    responses={
        200: {
            "description": "User profile fetched.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Profile fetched successfully",
                        "data": {
                            "id": 1,
                            "username": "john_doe",
                            "email": "john@example.com",
                        },
                    }
                }
            },
        },
        401: {"description": "Unauthorized or expired JWT token."},
    },
)
@router.get("/auth/me", tags=["Authentication"], include_in_schema=False)
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


@router.get(
    "/admin/profile",
    summary="Get Admin Profile",
    description="Retrieve administrative account details. Requires Admin JWT Bearer credentials (`is_admin=True`).",
    response_description="Authenticated admin profile object",
    tags=["Authentication"],
    responses={
        200: {
            "description": "Admin profile fetched.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Admin authorized successfully",
                        "data": {
                            "id": 1,
                            "username": "admin_master",
                            "email": "admin@ekarthub.com",
                            "is_admin": True,
                        },
                    }
                }
            },
        },
        401: {"description": "Unauthorized."},
        403: {"description": "Forbidden: Requires administrative privileges."},
    },
)
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


@router.get(
    "/test-token",
    summary="Test Token Secret Key Initialization",
    description="Internal diagnostic endpoint verifying JWT secret key configuration.",
    tags=["Authentication"],
    include_in_schema=False,
)
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
