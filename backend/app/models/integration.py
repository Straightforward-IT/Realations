"""Persistent integration state.

Every third-party connection (Microsoft Graph, Asana, Pipedrive, etc.) and
every outbound webhook subscription (Zapier or otherwise) is recorded as a
tenant-scoped row so the integration framework can iterate connections at
dispatch time without a hard-coded registry.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin, new_uuid


class IntegrationConnection(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "integration_connections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "name", name="uq_integration_tenant_provider_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    # Slug of the provider plugin (e.g. "microsoft_graph", "asana", "pipedrive").
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # Provider-specific opaque configuration payload (refresh tokens, workspace ids, etc.).
    # In production this MUST be encrypted at rest by the platform's KMS layer.
    config: Mapped[dict] = mapped_column(default=dict, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)


class WebhookEndpoint(Base, TenantScopedMixin, TimestampMixin):
    """A subscription describing where to deliver outbound platform events.

    This is what backs Zapier-style and other generic HTTP automation
    integrations: external automations register a URL + a list of event types
    and Realations POSTs JSON envelopes to it whenever those events occur.
    """

    __tablename__ = "webhook_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str] = mapped_column(String(128), nullable=False)
    # Comma-separated list of event names this endpoint subscribes to, e.g.
    # "contact.created,deal.updated". The asterisk "*" matches all events.
    event_types: Mapped[str] = mapped_column(String(512), nullable=False, default="*")
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
