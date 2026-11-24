"""Authentication routes: register, login, and current user profile."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister
from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> User:
    """Register a new user account."""
    try:
        return register_user(db, payload)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate user credentials and issue a JWT access token."""
    try:
        user = authenticate_user(db, payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user
