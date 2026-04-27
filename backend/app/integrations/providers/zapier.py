"""Zapier integration provider.

Zapier and the wider "make.com / n8n" automation ecosystem don't need a
bespoke API client — they consume generic outbound webhooks. We register
``ZapierProvider`` so it appears in the providers catalogue and so we can
attach Zapier-specific niceties (e.g. Zap-friendly payload shapes), but the
heavy lifting is performed by :class:`app.integrations.base.EventBus`'s
generic webhook dispatcher reading from the ``WebhookEndpoint`` table.
"""

from __future__ import annotations

import logging

from app.integrations.base import (
    IntegrationContext,
    IntegrationEvent,
    IntegrationProvider,
    register_provider,
)
from app.licensing.catalog import F_INTEGRATIONS_ZAPIER

log = logging.getLogger(__name__)


@register_provider
class ZapierProvider(IntegrationProvider):
    slug = "zapier"
    display_name = "Zapier"
    feature_key = F_INTEGRATIONS_ZAPIER
    required_config_keys = ()

    def on_event(self, ctx: IntegrationContext, event: IntegrationEvent) -> None:
        # No-op: outbound delivery to the Zap subscription URL is handled by
        # the generic WebhookEndpoint dispatcher in EventBus.
        log.debug(
            "[zapier] tenant=%s event=%s (delivery handled by webhook bus)",
            event.tenant_id,
            event.name,
        )
