"""Authentication service for registration and credential verification."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    normalize_email,
    verify_dummy_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import UserLogin, UserRegister


class EmailAlreadyRegisteredError(Exception):
    """Raised when attempting to register with an email already in use."""


class InvalidCredentialsError(Exception):
    """Raised when login fails due to unknown email or wrong password."""


def register_user(db: Session, payload: UserRegister) -> User:
    """Create a new user with normalized email and bcrypt password hash."""
    normalized = normalize_email(str(payload.email))
    existing = db.scalar(select(User).where(User.email == normalized))
    if existing is not None:
        raise EmailAlreadyRegisteredError("El correo ya está registrado.")

    user = User(
        email=normalized,
        password_hash=hash_password(payload.password),
        annual_inflation_rate=payload.annual_inflation_rate,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyRegisteredError("El correo ya está registrado.") from exc

    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: UserLogin) -> User:
    """Validate credentials without leaking whether the email exists."""
    normalized = normalize_email(str(payload.email))
    user = db.scalar(select(User).where(User.email == normalized))
    if user is None:
        verify_dummy_password(payload.password)
        raise InvalidCredentialsError("Credenciales inválidas.")

    if not verify_password(payload.password, user.password_hash):
        raise InvalidCredentialsError("Credenciales inválidas.")

    return user
