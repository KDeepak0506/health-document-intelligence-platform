from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.auth_service import login_user, register_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
)
def register_endpoint(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    return register_user(db=db, user_in=user_in)


@router.post(
    "/login",
    response_model=Token,
)
def login_endpoint(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm exposes the submitted email as `username`,
    # which also lets Swagger's built-in "Authorize" button work out of the box.
    access_token = login_user(
        db=db,
        email=form_data.username,
        password=form_data.password,
    )

    return Token(access_token=access_token)