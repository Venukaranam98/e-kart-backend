from fastapi import APIRouter, HTTPException, status, Depends

from sqlalchemy.orm import Session

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm
)

from database import get_db

from schemas import (
    UserSchema
)

from models import User

from hashing import (
    hash_password,
    verify_password
)

from jwt_handler import (
    create_access_token,
    verify_access_token
)

from redis_client import redis_client


router = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)



@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"]
)

def register(
    user: UserSchema,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:

        raise HTTPException(

            status_code=400,

            detail={

                "success": False,

                "message": "Email already registered",


            }

        )

    hashed_password = hash_password(
        user.password
    )

    new_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    access_token = create_access_token(
        data={
            "sub": new_user.email
        }
    )

    return {

    "success": True,

    "message": "Registration Successful",

    "data": {

        "access_token": access_token,

        "token_type": "bearer"

    }

}

    


@router.post(
    "/login",
    tags=["Authentication"]
)
def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    attempts_key = f"login_attempts:{request.username}"

    attempts = redis_client.get(attempts_key)

    if attempts and int(attempts) >= 5:
        raise HTTPException(
            status_code=429,
            detail={
                "success": False,
                "message": "Too many failed login attempts. Try again in 15 minutes."
            }
        )

    existing_user = db.query(User).filter(
        User.email == request.username
    ).first()

    if not existing_user:

        redis_client.incr(attempts_key)
        redis_client.expire(attempts_key, 900)

        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "User not found"
            }
        )

    password_valid = verify_password(
        request.password,
        existing_user.password
    )

    if not password_valid:

        redis_client.incr(attempts_key)
        redis_client.expire(attempts_key, 900)

        remaining = 5 - int(redis_client.get(attempts_key))

        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": f"Invalid password. {remaining} attempts remaining."
            }
        )

    redis_client.delete(attempts_key)

    access_token = create_access_token(
        data={
            "sub": existing_user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
    


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    email = verify_access_token(token)

    if email is None:

        raise HTTPException(

            status_code=401,

            detail={

                "success": False,

                "message": "Invalid Token",


            }

        )

    user = db.query(User).filter(
        User.email == email
    ).first()

    return user


@router.get(
    "/profile",
    tags=["Authentication"]
)

def get_profile(
    current_user: User = Depends(get_current_user)
):

    return {

        "success": True,

        "message": "Profile fetched successfully",

        "data": {

            "id": current_user.id,

            "username": current_user.username,

            "email": current_user.email

        }

    }


def get_current_admin(

    current_user: User = Depends(
        get_current_user
    )

):

    if not current_user.is_admin:

        raise HTTPException(

            status_code=403,

            detail={

                "success": False,

                "message": "Not authorized",


            }

        )

    return current_user


@router.get(
    "/admin/profile",
    tags=["Authentication"]
)

def admin_profile(

    current_admin: User = Depends(
        get_current_admin
    )

):

    return {

        "success": True,

        "message": "Admin authorized successfully",

        "data": {

            "id": current_admin.id,

            "username": current_admin.username,

            "email": current_admin.email,

            "is_admin": current_admin.is_admin

        }

    }

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    print("TOKEN RECEIVED:", token)

    email = verify_access_token(token)

    print("EMAIL:", email)

    if email is None:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": "Invalid Token",
            }
        )

    user = db.query(User).filter(
        User.email == email
    ).first()

    return user

@router.get("/test-token")
def test_token():
    from jwt_handler import SECRET_KEY

    return {
        "secret_key": SECRET_KEY
    }