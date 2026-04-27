"""Convenience wrappers around the integration EventBus."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.base import EventBus, IntegrationEvent


def publish_event(session: Session, *, name: str, tenant_id: uuid.UUID, payload: dict[str, Any]) -> None:
    """Publish a CRM event to all enabled providers and webhook subscribers."""
    with EventBus(session) as bus:
        bus.publish(IntegrationEvent(name=name, tenant_id=tenant_id, payload=payload))
