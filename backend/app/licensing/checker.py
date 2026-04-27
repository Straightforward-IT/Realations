"""Runtime license / subscription enforcement helpers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import LicenseError
from app.models.contact import Contact
from app.models.integration import IntegrationConnection
from app.models.subscription import Plan, Subscription
from app.models.user import User


@dataclass
class LicenseChecker:
    """Tenant-scoped helper used by the API to enforce subscription rules.

    A ``LicenseChecker`` is constructed per request after the tenant has been
    resolved from the access token (see :func:`app.api.deps.get_license`). It
    eagerly loads the tenant's active plan so subsequent ``require_*`` calls
    are O(1) for feature checks and a single ``COUNT`` query for resource
    limit checks.
    """

    session: Session
    tenant_id: uuid.UUID
    plan: Plan
    subscription: Subscription

    # ---- feature flags ---------------------------------------------------

    def has_feature(self, key: str) -> bool:
        return bool((self.plan.features or {}).get(key, False))

    def require_feature(self, key: str) -> None:
        if not self.has_feature(key):
            raise LicenseError(
                f"Plan '{self.plan.code}' does not include the '{key}' feature."
            )

    # ---- resource limits -------------------------------------------------

    def _count(self, model) -> int:
        # NOTE: All tenant-scoped models carry a ``tenant_id`` column. We bind
        # it explicitly here rather than relying on RLS so the same code path
        # works on PostgreSQL and on the SQLite test backend.
        stmt = select(func.count()).select_from(model).where(model.tenant_id == self.tenant_id)
        return int(self.session.execute(stmt).scalar_one())

    def require_capacity_for_user(self) -> None:
        if self.plan.max_users is None:
            return
        if self._count(User) >= self.plan.max_users:
            raise LicenseError(
                f"Plan '{self.plan.code}' allows at most {self.plan.max_users} users."
            )

    def require_capacity_for_contact(self) -> None:
        if self.plan.max_contacts is None:
            return
        if self._count(Contact) >= self.plan.max_contacts:
            raise LicenseError(
                f"Plan '{self.plan.code}' allows at most {self.plan.max_contacts} contacts."
            )

    def require_capacity_for_integration(self) -> None:
        if self.plan.max_integrations is None:
            return
        if self._count(IntegrationConnection) >= self.plan.max_integrations:
            raise LicenseError(
                f"Plan '{self.plan.code}' allows at most {self.plan.max_integrations} integrations."
            )


def get_license_checker(session: Session, tenant_id: uuid.UUID) -> LicenseChecker:
    """Construct a :class:`LicenseChecker` for the given tenant.

    Raises :class:`LicenseError` if the tenant has no active subscription —
    callers expect every authenticated tenant to be billable.
    """
    sub = session.execute(
        select(Subscription).where(Subscription.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if sub is None:
        raise LicenseError("Tenant has no active subscription.")
    if sub.status not in {"active", "trialing"}:
        raise LicenseError(f"Tenant subscription status is '{sub.status}'.")
    plan = session.get(Plan, sub.plan_id)
    if plan is None or not plan.is_active:
        raise LicenseError("Subscription references an inactive plan.")
    return LicenseChecker(session=session, tenant_id=tenant_id, plan=plan, subscription=sub)
