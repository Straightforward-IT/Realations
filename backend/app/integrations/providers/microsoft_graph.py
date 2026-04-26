"""Microsoft Graph integration provider scaffold.

This wires Realations to Microsoft 365 (mail, calendar, contacts) via Graph.
Production deployments should plug an OAuth2 authorization-code flow into
the ``config`` blob (storing refresh tokens) and replace the no-op hooks with
real Graph API calls.
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
from app.licensing.catalog import F_INTEGRATIONS_MS_GRAPH

log = logging.getLogger(__name__)


@register_provider
class MicrosoftGraphProvider(IntegrationProvider):
    slug = "microsoft_graph"
    display_name = "Microsoft Graph"
    feature_key = F_INTEGRATIONS_MS_GRAPH
    required_config_keys = ("tenant_id", "client_id", "client_secret")

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    def on_event(self, ctx: IntegrationContext, event: IntegrationEvent) -> None:
        # Example wiring: when a contact is created in Realations, mirror it
        # into the connected Microsoft 365 contacts folder. The real call would
        # be:
        #   POST {GRAPH_BASE_URL}/me/contacts
        # using the access token derived from ctx.connection.config.
        log.info(
            "[microsoft_graph] tenant=%s event=%s (would call %s)",
            event.tenant_id,
            event.name,
            self.GRAPH_BASE_URL,
        )

    def handle_inbound(self, ctx: IntegrationContext, payload: dict[str, Any]) -> dict[str, Any]:
        # Microsoft Graph subscriptions deliver change notifications here.
        return {"received": True, "items": len(payload.get("value", []) or [])}
