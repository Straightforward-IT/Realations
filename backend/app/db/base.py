"""Declarative base and shared SQLAlchemy types."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's native UUID type when available and falls back to a
    36-character string column elsewhere (notably SQLite for tests).
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class JSONB_(TypeDecorator):
    """JSONB on PostgreSQL, generic JSON elsewhere.

    Per the architectural blueprint, custom-attribute payloads live in JSONB
    columns so PostgreSQL's GIN indexes can serve nested key/value queries with
    near-native performance.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Common declarative base for all ORM models."""

    type_annotation_map = {
        uuid.UUID: GUID(),
        dict: JSONB_(),
    }


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class TenantScopedMixin:
    """Marker mixin: every concrete model carrying a ``tenant_id`` column."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True, nullable=False)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()
