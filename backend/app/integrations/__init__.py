"""Pluggable third-party integration framework.

The framework follows a registry pattern: each provider subclass declares a
``slug`` and is automatically discoverable via :func:`get_provider`. The API
layer wires CRM events into provider hooks through :class:`EventBus`, which
also dispatches generic outbound HTTP webhooks (the Zapier-style escape hatch).
"""

from app.integrations.base import (  # noqa: F401
    EventBus,
    IntegrationContext,
    IntegrationEvent,
    IntegrationProvider,
    get_provider,
    list_providers,
    register_provider,
)
from app.integrations.providers import (  # noqa: F401
    AsanaProvider,
    MicrosoftGraphProvider,
    PipedriveProvider,
    ZapierProvider,
)
