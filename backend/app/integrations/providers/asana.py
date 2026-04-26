"""Asana integration provider scaffold."""

from __future__ import annotations

import logging
from typing import Any

from app.integrations.base import (
    IntegrationContext,
    IntegrationEvent,
    IntegrationProvider,
    register_provider,
)
from app.licensing.catalog import F_INTEGRATIONS_ASANA

log = logging.getLogger(__name__)


@register_provider
class AsanaProvider(IntegrationProvider):
    slug = "asana"
    display_name = "Asana"
    feature_key = F_INTEGRATIONS_ASANA
    required_config_keys = ("personal_access_token", "workspace_gid")

    API_BASE_URL = "https://app.asana.com/api/1.0"

    def on_event(self, ctx: IntegrationContext, event: IntegrationEvent) -> None:
        # Example wiring: when a Deal is created in Realations, push a task
        # into the configured Asana project for follow-up. Production code
        # would POST {API_BASE_URL}/tasks with auth.
        if not event.name.startswith("deal."):
            return
        log.info(
            "[asana] tenant=%s would create task for event=%s in workspace=%s",
            event.tenant_id,
            event.name,
            ctx.connection.config.get("workspace_gid"),
        )

    def handle_inbound(self, ctx: IntegrationContext, payload: dict[str, Any]) -> dict[str, Any]:
        # Asana sends webhook handshake events containing X-Hook-Secret.
        return {"received": True, "events": len(payload.get("events", []) or [])}
