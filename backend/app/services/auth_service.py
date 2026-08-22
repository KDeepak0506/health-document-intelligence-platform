from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import UserCreate


def register_user(
    db: Session,
    user_in: UserCreate,
) -> User:

    existing_user = (
        db.query(User)
        .filter(User.email == user_in.email)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Email is already registered",
        )

    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        role=user_in.role.value,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:

    user = db.query(User).filter(User.email == email).first()

    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def login_user(
    db: Session,
    email: str,
    password: str,
) -> str:

    user = authenticate_user(db, email=email, password=password)

    return create_access_token(subject=str(user.user_id))