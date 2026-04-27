"""Subscription plan and tenant subscription models.

The licensing module ships with a small catalogue of canonical tiers
(see :mod:`app.licensing.catalog`) but the ``Plan`` table is intentionally
data-driven so operators can publish bespoke plans without code changes.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class Plan(Base, TimestampMixin):
    """A licensing plan/tier offered by the platform."""

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # Soft caps. ``None`` represents an unlimited allowance for that resource.
    max_users: Mapped[int | None] = mapped_column(Integer)
    max_contacts: Mapped[int | None] = mapped_column(Integer)
    max_integrations: Mapped[int | None] = mapped_column(Integer)
    # Boolean feature flags toggled by the catalogue. Flat key/value JSON keeps
    # it cheap to add new flags without schema migrations.
    features: Mapped[dict] = mapped_column(default=dict, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class Subscription(Base, TimestampMixin):
    """A tenant's currently active subscription to a plan."""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, index=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"))
    # Subscription lifecycle status. One of: active | trialing | past_due | cancelled.
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False, nullable=False)
