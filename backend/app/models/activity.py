"""Activity / interaction log entry.

In a production deployment, the activity stream is the workload most likely to
be moved off the relational core into TimescaleDB or ClickHouse (per the
"Managing Telemetry" section of the architectural blueprint). The model here is
deliberately small and append-friendly so that migration remains mechanical.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin, new_uuid


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Activity(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("contacts.id", ondelete="SET NULL"))
    deal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("deals.id", ondelete="SET NULL"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # call|email|note|task|meeting
    subject: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    body: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )
    payload: Mapped[dict] = mapped_column(default=dict, nullable=False)
