"""Subscription / plan management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db
from app.core.errors import NotFoundError, PermissionDeniedError
from app.licensing.catalog import seed_plans
from app.models.subscription import Plan, Subscription
from app.schemas.subscription import PlanRead, SubscriptionAssign, SubscriptionRead

router = APIRouter()


@router.get("/plans", response_model=list[PlanRead])
def list_plans(session: Session = Depends(get_db)) -> list[Plan]:
    """Catalog of available plans (publicly readable)."""
    plans = list(session.execute(select(Plan).where(Plan.is_active.is_(True))).scalars())
    if not plans:
        # Lazy-seed on first call so a fresh DB still surfaces plan options.
        seed_plans(session)
        session.commit()
        plans = list(session.execute(select(Plan).where(Plan.is_active.is_(True))).scalars())
    return plans


@router.get("/me", response_model=SubscriptionRead)
def get_my_subscription(
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Subscription:
    sub = session.execute(
        select(Subscription).where(Subscription.tenant_id == current.tenant_id)
    ).scalar_one_or_none()
    if sub is None:
        raise NotFoundError("Tenant has no subscription on file.")
    return sub


@router.put("/me", response_model=SubscriptionRead)
def assign_my_subscription(
    payload: SubscriptionAssign,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Subscription:
    """Switch the active tenant to a different plan.

    In production this would be invoked by the billing service, not the
    customer directly; we restrict to admins as a sensible default.
    """
    if current.user.role != "admin":
        raise PermissionDeniedError("Only tenant admins can change the subscription plan.")

    plan = session.execute(select(Plan).where(Plan.code == payload.plan_code)).scalar_one_or_none()
    if plan is None or not plan.is_active:
        raise NotFoundError(f"Plan '{payload.plan_code}' is not available.")

    sub = session.execute(
        select(Subscription).where(Subscription.tenant_id == current.tenant_id)
    ).scalar_one_or_none()
    if sub is None:
        sub = Subscription(tenant_id=current.tenant_id, plan_id=plan.id, status="active")
        session.add(sub)
    else:
        sub.plan_id = plan.id
        sub.status = "active"
    session.commit()
    session.refresh(sub)
    return sub
