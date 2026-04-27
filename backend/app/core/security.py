"""Password hashing and JWT helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd_context.verify(plain, hashed)
    except ValueError:
        # Malformed hash on disk should never authenticate.
        return False


def create_access_token(
    *,
    subject: str,
    tenant_id: str,
    extra_claims: dict[str, Any] | None = None,
    ttl: timedelta | None = None,
) -> str:
    """Mint a signed JWT carrying the user identity and active tenant context.

    Tenant id is embedded in the token so the API layer can authoritatively
    bind every request to a single tenant before any DB query is issued.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    expires = now + (ttl or timedelta(minutes=settings.access_token_ttl_minutes))
    payload: dict[str, Any] = {
        "sub": subject,
        "tid": tenant_id,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
