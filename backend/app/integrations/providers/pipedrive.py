"""Pipedrive integration provider scaffold.

Useful for migrating customers off Pipedrive (read their deals into Realations)
or for keeping the two systems in lockstep during transition periods.
"""

from __future__ import annotations

import logging
from typing import Any

from app.integrations.base import (
    IntegrationContext,
    IntegrationEvent,
    IntegrationProvider,
    register_provider,
)
from app.licensing.catalog import F_INTEGRATIONS_PIPEDRIVE

log = logging.getLogger(__name__)


@register_provider
class PipedriveProvider(IntegrationProvider):
    slug = "pipedrive"
    display_name = "Pipedrive"
    feature_key = F_INTEGRATIONS_PIPEDRIVE
    required_config_keys = ("api_token", "company_domain")

    @property
    def api_base_url(self) -> str:
        return "https://{domain}.pipedrive.com/api/v1"

    def on_event(self, ctx: IntegrationContext, event: IntegrationEvent) -> None:
        # Example: mirror new contacts/deals into Pipedrive via /persons or /deals endpoints.
        log.info("[pipedrive] tenant=%s event=%s would sync to Pipedrive", event.tenant_id, event.name)

    def handle_inbound(self, ctx: IntegrationContext, payload: dict[str, Any]) -> dict[str, Any]:
        # Pipedrive webhooks contain {"event": "...", "current": {...}, "previous": {...}}.
        return {"received": True, "event": payload.get("event")}
