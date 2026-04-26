"""Integration framework primitives: events, provider base class, event bus."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, ClassVar

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import IntegrationError
from app.licensing.catalog import (
    F_INTEGRATIONS_ASANA,
    F_INTEGRATIONS_MS_GRAPH,
    F_INTEGRATIONS_PIPEDRIVE,
    F_INTEGRATIONS_ZAPIER,
)
from app.models.integration import IntegrationConnection, WebhookEndpoint

log = logging.getLogger(__name__)


@dataclass
class IntegrationEvent:
    """A normalized internal event suitable for outbound dispatch."""

    name: str  # e.g. "contact.created", "deal.updated"
    tenant_id: uuid.UUID
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_envelope(self) -> dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "event": self.name,
            "tenant_id": str(self.tenant_id),
            "occurred_at": self.occurred_at.isoformat(),
            "data": self.payload,
        }


@dataclass
class IntegrationContext:
    """Per-call context handed to provider hooks."""

    session: Session
    connection: IntegrationConnection


# ---------------------------------------------------------------------------
# Provider base + registry
# ---------------------------------------------------------------------------


_REGISTRY: dict[str, type[IntegrationProvider]] = {}


def register_provider(cls: type[IntegrationProvider]) -> type[IntegrationProvider]:
    """Decorator registering a provider in the global lookup."""
    if not cls.slug:
        raise ValueError(f"{cls.__name__}.slug must be set")
    if cls.slug in _REGISTRY:
        raise ValueError(f"Duplicate integration provider slug: {cls.slug}")
    _REGISTRY[cls.slug] = cls
    return cls


def get_provider(slug: str) -> type[IntegrationProvider] | None:
    return _REGISTRY.get(slug)


def list_providers() -> list[type[IntegrationProvider]]:
    return sorted(_REGISTRY.values(), key=lambda c: c.slug)


class IntegrationProvider:
    """Base class for third-party integrations.

    Subclasses override :attr:`slug`, :attr:`feature_key`, and the lifecycle
    hooks they care about. The default implementations no-op so providers can
    opt in incrementally.
    """

    slug: ClassVar[str] = ""
    display_name: ClassVar[str] = ""
    feature_key: ClassVar[str] = ""  # license feature flag gating this provider
    required_config_keys: ClassVar[tuple[str, ...]] = ()

    # ---- lifecycle ------------------------------------------------------

    @classmethod
    def validate_config(cls, config: dict[str, Any]) -> None:
        """Validate the config blob stored on :class:`IntegrationConnection`.

        Default behaviour: every key listed in :attr:`required_config_keys`
        must be present and truthy. Subclasses may override for richer rules.
        """
        missing = [k for k in cls.required_config_keys if not config.get(k)]
        if missing:
            raise IntegrationError(
                f"Missing required config for {cls.slug}: {', '.join(missing)}"
            )

    # ---- event hooks ----------------------------------------------------

    def on_event(self, ctx: IntegrationContext, event: IntegrationEvent) -> None:
        """Handle a CRM event. Default no-op."""

    # ---- inbound webhook handling --------------------------------------

    def handle_inbound(self, ctx: IntegrationContext, payload: dict[str, Any]) -> dict[str, Any]:
        """Process a payload delivered by the third party. Default echoes input."""
        return {"received": True, "echo": payload}


# ---------------------------------------------------------------------------
# Event bus
# ---------------------------------------------------------------------------


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _matches_event(subscribed: str, event_name: str) -> bool:
    """Return True if the comma-separated subscription matches ``event_name``.

    ``"*"`` matches anything; ``"contact.*"`` matches any ``contact.<x>`` event;
    exact matches always win.
    """
    for raw in subscribed.split(","):
        token = raw.strip()
        if not token:
            continue
        if token == "*" or token == event_name:
            return True
        if token.endswith(".*") and event_name.startswith(token[:-1]):
            return True
    return False


class EventBus:
    """Dispatches :class:`IntegrationEvent` instances to providers and webhooks.

    The bus is intentionally synchronous: production deployments should swap
    :meth:`publish` for a Celery/RQ/Kafka producer, but the public API and
    contract — fan out to enabled provider connections, then to active webhook
    subscribers — remains identical.
    """

    def __init__(self, session: Session, *, http_client: httpx.Client | None = None) -> None:
        self.session = session
        self._http = http_client
        self._owns_http = http_client is None

    def __enter__(self) -> EventBus:
        if self._http is None:
            self._http = httpx.Client(timeout=get_settings().webhook_timeout_seconds)
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._owns_http and self._http is not None:
            self._http.close()
            self._http = None

    # ---- public API -----------------------------------------------------

    def publish(self, event: IntegrationEvent) -> dict[str, Any]:
        """Fan out one event. Returns a small delivery report (useful in tests)."""
        connections = self._load_connections(event.tenant_id)
        webhooks = self._load_webhooks(event.tenant_id)

        provider_results: list[dict[str, Any]] = []
        for conn in connections:
            provider_cls = get_provider(conn.provider)
            if provider_cls is None:
                log.warning("Unknown integration provider on connection: %s", conn.provider)
                continue
            try:
                provider_cls().on_event(IntegrationContext(self.session, conn), event)
                provider_results.append({"provider": conn.provider, "status": "ok"})
            except Exception as exc:  # pragma: no cover - defensive
                log.exception("Provider %s failed handling %s", conn.provider, event.name)
                provider_results.append(
                    {"provider": conn.provider, "status": "error", "error": str(exc)}
                )

        webhook_results = list(self._dispatch_webhooks(webhooks, event))
        return {"providers": provider_results, "webhooks": webhook_results}

    # ---- helpers --------------------------------------------------------

    def _load_connections(self, tenant_id: uuid.UUID) -> list[IntegrationConnection]:
        stmt = select(IntegrationConnection).where(
            IntegrationConnection.tenant_id == tenant_id,
            IntegrationConnection.is_enabled.is_(True),
        )
        return list(self.session.execute(stmt).scalars())

    def _load_webhooks(self, tenant_id: uuid.UUID) -> list[WebhookEndpoint]:
        stmt = select(WebhookEndpoint).where(
            WebhookEndpoint.tenant_id == tenant_id,
            WebhookEndpoint.is_active.is_(True),
        )
        return list(self.session.execute(stmt).scalars())

    def _dispatch_webhooks(
        self, webhooks: Iterable[WebhookEndpoint], event: IntegrationEvent
    ) -> Iterable[dict[str, Any]]:
        if self._http is None:
            self._http = httpx.Client(timeout=get_settings().webhook_timeout_seconds)
            self._owns_http = True

        envelope = event.to_envelope()
        body = json.dumps(envelope, separators=(",", ":")).encode("utf-8")

        for hook in webhooks:
            if not _matches_event(hook.event_types, event.name):
                continue
            signature = _sign(hook.secret, body)
            headers = {
                "Content-Type": "application/json",
                "X-Realations-Event": event.name,
                "X-Realations-Signature": f"sha256={signature}",
                "X-Realations-Delivery": envelope["id"],
            }
            try:
                resp = self._http.post(hook.target_url, content=body, headers=headers)
                yield {
                    "endpoint_id": str(hook.id),
                    "status_code": resp.status_code,
                    "ok": 200 <= resp.status_code < 300,
                }
            except httpx.HTTPError as exc:
                log.warning("Webhook delivery to %s failed: %s", hook.target_url, exc)
                yield {"endpoint_id": str(hook.id), "ok": False, "error": str(exc)}


# Re-export feature keys so providers' ``feature_key`` declarations stay in sync.
__all_feature_keys__ = (
    F_INTEGRATIONS_MS_GRAPH,
    F_INTEGRATIONS_ASANA,
    F_INTEGRATIONS_PIPEDRIVE,
    F_INTEGRATIONS_ZAPIER,
)
