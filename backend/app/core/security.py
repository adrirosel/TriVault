"""Password hashing with bcrypt and JWT token handling with PyJWT."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings

MAX_BCRYPT_PASSWORD_BYTES = 72
_DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"trivault-dummy-password", bcrypt.gensalt()).decode("utf-8")


class TokenValidationError(Exception):
    """Raised when an access token is missing, malformed, expired, or invalid."""


def normalize_email(email: str) -> str:
    """Normalize email addresses consistently across registration and login."""
    return email.strip().lower()


def validate_password_byte_length(password: str) -> None:
    """Ensure password does not exceed bcrypt's 72-byte UTF-8 input limit."""
    if len(password.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError(
            f"Password cannot exceed {MAX_BCRYPT_PASSWORD_BYTES} bytes in UTF-8."
        )


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    validate_password_byte_length(password)
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    encoded_password = plain_password.encode("utf-8")
    if len(encoded_password) > MAX_BCRYPT_PASSWORD_BYTES:
        return False
    return bcrypt.checkpw(encoded_password, password_hash.encode("utf-8"))


def verify_dummy_password(plain_password: str) -> None:
    """Run a constant-cost bcrypt check when a user record does not exist."""
    verify_password(plain_password, _DUMMY_PASSWORD_HASH)


def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed HS256 JWT access token for a given user ID."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """Validate signature, expiry, token type, and return the user ID from sub."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )
    except InvalidTokenError as exc:
        raise TokenValidationError("Invalid or expired token.") from exc

    if payload.get("type") != "access":
        raise TokenValidationError("Invalid token type.")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise TokenValidationError("Invalid token subject.")

    user_id = int(subject)
    if user_id <= 0:
        raise TokenValidationError("Invalid token subject.")
    return user_id
