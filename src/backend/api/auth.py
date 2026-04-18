"""JWT authentication utilities — password hashing, JWT encode/decode."""

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from pydantic import BaseModel

from backend.config import get_settings

# JWT settings
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(user_id: str, secret_key: str) -> str:
    """Create a JWT access token for a user."""
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, secret_key, algorithm=JWT_ALGORITHM)


def decode_token(token: str, secret_key: str) -> TokenPayload | None:
    """Decode and validate a JWT token. Returns None if invalid or expired."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return None


def get_jwt_secret_key() -> str:
    """Get JWT secret key from settings, with validation."""
    settings = get_settings()
    if not settings.jwt_secret_key:
        logging.warning(
            "JWT_SECRET_KEY not set in environment — "
            "using a default for development only. "
            "Set JWT_SECRET_KEY in production (.env file)!"
        )
        # Return a deterministic dev key so tests can run
        return "dev-only-secret-key-do-not-use-in-production"
    return settings.jwt_secret_key
