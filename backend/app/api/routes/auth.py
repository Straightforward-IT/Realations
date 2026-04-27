"""Auth: tenant bootstrap + login."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.errors import AuthError, ConflictError, NotFoundError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.subscription import Plan, Subscription
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterTenantRequest, TokenResponse
from app.schemas.user import UserRead

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_tenant(payload: RegisterTenantRequest, session: Session = Depends(get_db)) -> User:
    """Create a tenant + first admin user + assign a starting plan, atomically."""
    existing = session.execute(select(Tenant).where(Tenant.slug == payload.tenant_slug)).scalar_one_or_none()
    if existing is not None:
        raise ConflictError(f"Tenant slug '{payload.tenant_slug}' is already in use.")

    plan = session.execute(select(Plan).where(Plan.code == payload.plan_code)).scalar_one_or_none()
    if plan is None:
        raise NotFoundError(f"Plan '{payload.plan_code}' does not exist.")

    tenant = Tenant(name=payload.tenant_name, slug=payload.tenant_slug)
    session.add(tenant)
    session.flush()  # populate tenant.id

    user = User(
        tenant_id=tenant.id,
        email=payload.admin_email.lower(),
        full_name=payload.admin_full_name,
        hashed_password=hash_password(payload.admin_password),
        role="admin",
    )
    session.add(user)

    session.add(Subscription(tenant_id=tenant.id, plan_id=plan.id, status="active"))

    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db)) -> TokenResponse:
    tenant = session.execute(select(Tenant).where(Tenant.slug == payload.tenant_slug)).scalar_one_or_none()
    if tenant is None or not tenant.is_active:
        # Avoid leaking which of the three (tenant / email / password) failed.
        raise AuthError("Invalid credentials")

    user = session.execute(
        select(User).where(User.tenant_id == tenant.id, User.email == payload.email.lower())
    ).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise AuthError("Invalid credentials")

    token = create_access_token(subject=str(user.id), tenant_id=str(tenant.id))
    return TokenResponse(
        access_token=token,
        expires_in=get_settings().access_token_ttl_minutes * 60,
    )
