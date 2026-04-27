"""Integration framework tests: provider registry, event bus, webhook signing."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from unittest.mock import MagicMock

import httpx
import pytest

from app.db import session as db_session
from app.integrations.base import (
    EventBus,
    IntegrationContext,
    IntegrationEvent,
    IntegrationProvider,
    _matches_event,
    get_provider,
    list_providers,
    register_provider,
)
from app.licensing.catalog import F_INTEGRATIONS_ZAPIER
from app.models.integration import IntegrationConnection, WebhookEndpoint
from app.models.tenant import Tenant


def _make_tenant(session) -> Tenant:
    t = Tenant(name="Bus Test", slug=f"bustest-{uuid.uuid4().hex[:8]}")
    session.add(t)
    session.commit()
    return t


def test_builtin_providers_are_registered():
    slugs = {p.slug for p in list_providers()}
    assert {"microsoft_graph", "asana", "pipedrive", "zapier"}.issubset(slugs)


def test_event_bus_dispatches_to_provider():
    calls: list[IntegrationEvent] = []

    @register_provider
    class _Recorder(IntegrationProvider):
        slug = f"recorder-{uuid.uuid4().hex[:6]}"
        display_name = "Recorder"
        feature_key = F_INTEGRATIONS_ZAPIER

        def on_event(self, ctx: IntegrationContext, event: IntegrationEvent) -> None:
            calls.append(event)

    with db_session.SessionLocal() as session:
        tenant = _make_tenant(session)
        session.add(
            IntegrationConnection(
                tenant_id=tenant.id, provider=_Recorder.slug, name="default", config={}, is_enabled=True
            )
        )
        session.commit()

        bus = EventBus(session)
        report = bus.publish(
            IntegrationEvent(name="contact.created", tenant_id=tenant.id, payload={"id": "x"})
        )

    assert len(calls) == 1
    assert calls[0].name == "contact.created"
    assert any(r["status"] == "ok" for r in report["providers"])

    # Ensure the registry has it before we drop it for hygiene.
    assert get_provider(_Recorder.slug) is _Recorder


def test_event_bus_signs_outbound_webhooks():
    captured: dict = {}

    def transport_handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["body"] = request.content
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(transport_handler)
    http = httpx.Client(transport=transport)

    with db_session.SessionLocal() as session:
        tenant = _make_tenant(session)
        secret = "topsecret"
        session.add(
            WebhookEndpoint(
                tenant_id=tenant.id,
                target_url="https://example.test/hook",
                secret=secret,
                event_types="contact.*",
                is_active=True,
            )
        )
        session.commit()

        with EventBus(session, http_client=http) as bus:
            event = IntegrationEvent(name="contact.created", tenant_id=tenant.id, payload={"id": "1"})
            report = bus.publish(event)

    http.close()

    assert any(r.get("ok") for r in report["webhooks"])
    expected_sig = hmac.new(b"topsecret", captured["body"], hashlib.sha256).hexdigest()
    assert captured["headers"]["x-realations-signature"] == f"sha256={expected_sig}"
    assert captured["headers"]["x-realations-event"] == "contact.created"
    payload = json.loads(captured["body"])
    assert payload["event"] == "contact.created"
    assert payload["data"] == {"id": "1"}


def test_event_bus_skips_non_matching_subscriptions():
    captured = MagicMock()

    def transport_handler(request: httpx.Request) -> httpx.Response:
        captured(request)
        return httpx.Response(200)

    transport = httpx.MockTransport(transport_handler)
    http = httpx.Client(transport=transport)

    with db_session.SessionLocal() as session:
        tenant = _make_tenant(session)
        session.add(
            WebhookEndpoint(
                tenant_id=tenant.id,
                target_url="https://example.test/h",
                secret="s",
                event_types="deal.created",  # <- only deal.created
                is_active=True,
            )
        )
        session.commit()

        with EventBus(session, http_client=http) as bus:
            bus.publish(IntegrationEvent(name="contact.created", tenant_id=tenant.id, payload={}))

    http.close()
    captured.assert_not_called()


@pytest.mark.parametrize(
    ("subscribed", "event", "expected"),
    [
        ("*", "contact.created", True),
        ("contact.created", "contact.created", True),
        ("contact.*", "contact.created", True),
        ("contact.*", "deal.created", False),
        ("deal.created,contact.created", "contact.created", True),
        ("", "contact.created", False),
    ],
)
def test_matches_event(subscribed, event, expected):
    assert _matches_event(subscribed, event) is expected
