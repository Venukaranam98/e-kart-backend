from fastapi import APIRouter, HTTPException, status, Depends

from sqlalchemy.orm import Session

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm
)

from database import get_db

from schemas import (
    UserSchema,
    UserResponse
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


router = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)


# REGISTER API

@router.post(
    "/register",
    response_model=UserResponse,
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
            detail="Email already registered"
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


    return new_user



@router.post(
    "/login",
    tags=["Authentication"]
)

def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == request.username
    ).first()


    if not existing_user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    password_valid = verify_password(
        request.password,
        existing_user.password
    )


    if not password_valid:

        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )


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
            detail="Invalid token"
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
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }

def get_current_admin(

    current_user: User = Depends(

        get_current_user

    )

):

    if not current_user.is_admin:

        raise HTTPException(

            status_code=403,

            detail="Not authorized"

        )


    return current_user