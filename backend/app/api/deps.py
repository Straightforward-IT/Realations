"""FastAPI dependency wiring: DB session, current user, license checker."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.errors import AuthError
from app.core.security import decode_access_token
from app.db.session import SessionLocal, set_tenant_context
from app.licensing.checker import LicenseChecker, get_license_checker
from app.models.user import User


@dataclass
class CurrentUser:
    """Resolved request principal."""

    user: User
    tenant_id: uuid.UUID


def get_db() -> Iterator[Session]:
    """Yield a request-scoped DB session.

    Tenant binding is intentionally *not* performed here — it happens in
    :func:`get_current_user` after the JWT is validated, so unauthenticated
    routes (login, healthz) never accidentally bypass an unset tenant.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise AuthError("Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthError("Authorization header must be 'Bearer <token>'")
    return token


def get_current_user(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_db),
) -> CurrentUser:
    token = _extract_bearer(authorization)
    try:
        claims = decode_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Access token expired") from exc
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid access token") from exc

    try:
        user_id = uuid.UUID(claims["sub"])
        tenant_id = uuid.UUID(claims["tid"])
    except (KeyError, ValueError) as exc:
        raise AuthError("Malformed access token") from exc

    user = session.get(User, user_id)
    if user is None or not user.is_active or user.tenant_id != tenant_id:
        raise AuthError("User not found or inactive for the tenant in token")

    # Bind tenant to the connection so RLS policies (PostgreSQL) and any
    # ORM helpers see the active tenant for the lifetime of this request.
    set_tenant_context(session, tenant_id)

    return CurrentUser(user=user, tenant_id=tenant_id)


def get_license(
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> LicenseChecker:
    return get_license_checker(session, current.tenant_id)
