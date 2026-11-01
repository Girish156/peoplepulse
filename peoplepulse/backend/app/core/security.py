"""
JWT-based authentication and password utilities for PeoplePulse.

Demo users are defined here for convenience during development / demos.
In production replace this with a real user store backed by the database.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
import hashlib
import hmac

def get_password_hash(password: str) -> str:
    """Return a secure SHA-256 hash of *password* with salt."""
    salt = "peoplepulse_salt_2026"
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password*."""
    return hmac.compare_digest(get_password_hash(plain_password), hashed_password)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    :param data: Payload dict to encode.
    :param expires_delta: Token lifetime.  Defaults to
        ``settings.ACCESS_TOKEN_EXPIRE_MINUTES``.
    :returns: Encoded JWT string.
    """
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(tz=timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.

    :param token: Raw JWT string.
    :returns: Decoded payload dict.
    :raises JWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ---------------------------------------------------------------------------
# Demo user store
# ---------------------------------------------------------------------------
# Keys are lowercase email addresses.
# Passwords are stored in plain text here ONLY because this is demo data that
# the UI displays on a login splash screen.  A real deployment MUST replace
# this dict with database-backed hashed passwords.
DEMO_USERS: Dict[str, Dict[str, Any]] = {
    "admin@peoplepulse.demo": {
        "email": "admin@peoplepulse.demo",
        "password": "PeoplePulse2026!",
        "hashed_password": get_password_hash("PeoplePulse2026!"),
        "role": "admin",
        "name": "Alex Administrator",
        "employee_id": "EMP-000001",
    },
    "hr@peoplepulse.demo": {
        "email": "hr@peoplepulse.demo",
        "password": "PeoplePulse2026!",
        "hashed_password": get_password_hash("PeoplePulse2026!"),
        "role": "hr_partner",
        "name": "Hannah HR",
        "employee_id": "EMP-000004",
    },
    "manager@peoplepulse.demo": {
        "email": "manager@peoplepulse.demo",
        "password": "PeoplePulse2026!",
        "hashed_password": get_password_hash("PeoplePulse2026!"),
        "role": "manager",
        "name": "Michael Manager",
        "employee_id": "EMP-000002",
    },
    "employee@peoplepulse.demo": {
        "email": "employee@peoplepulse.demo",
        "password": "PeoplePulse2026!",
        "hashed_password": get_password_hash("PeoplePulse2026!"),
        "role": "employee",
        "name": "Emma Employee",
        "employee_id": "EMP-000003",
    },
}


def authenticate_demo_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate against the in-memory demo user store.

    :returns: User dict on success, None on failure.
    """
    user = DEMO_USERS.get(email.lower())
    if user is None:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user
