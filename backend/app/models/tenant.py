"""Tenant aggregate root.

A *tenant* is the top-level customer of the platform — typically a single
company subscribing to Realations. Every row in every other tenant-scoped
table carries this tenant's id and is filtered by Row-Level Security policies
(see ``migrations/versions/0002_rls_policies.py``).
"""

from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_uuid


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
