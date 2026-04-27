"""Company (organization) record within the CRM."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin, new_uuid


class Company(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(128))
    # Per the blueprint's "Dynamic Attributes Pattern": tenant-defined fields live in JSONB so
    # PostgreSQL GIN indexes can serve nested key/value queries without DDL migrations.
    custom_attributes: Mapped[dict] = mapped_column(default=dict, nullable=False)
