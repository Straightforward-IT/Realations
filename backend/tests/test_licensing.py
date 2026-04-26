"""Licensing enforcement tests."""

from __future__ import annotations

from tests.factories import bootstrap_tenant


def _create_contact(client, headers, *, email: str, custom: dict | None = None) -> int:
    body: dict = {"first_name": "C", "last_name": email, "email": email}
    if custom is not None:
        body["custom_attributes"] = custom
    resp = client.post("/api/v1/contacts", json=body, headers=headers)
    return resp.status_code


def test_free_plan_blocks_custom_fields_on_contacts(client):
    _, headers = bootstrap_tenant(client, slug="freeco", plan_code="free")
    code = _create_contact(client, headers, email="a@a.example", custom={"vip": True})
    # Free plan disallows custom_fields feature -> 402 Payment Required
    assert code == 402


def test_starter_plan_allows_custom_fields(client):
    _, headers = bootstrap_tenant(client, slug="starterco", plan_code="starter")
    code = _create_contact(client, headers, email="b@b.example", custom={"vip": True})
    assert code == 201


def test_changing_plan_unlocks_custom_fields(client):
    _, headers = bootstrap_tenant(client, slug="upgrader", plan_code="free")
    assert _create_contact(client, headers, email="x@x.example", custom={"k": 1}) == 402

    resp = client.put("/api/v1/subscriptions/me", json={"plan_code": "starter"}, headers=headers)
    assert resp.status_code == 200

    assert _create_contact(client, headers, email="y@y.example", custom={"k": 2}) == 201


def test_free_plan_blocks_microsoft_graph_integration(client):
    _, headers = bootstrap_tenant(client, slug="freegraph", plan_code="free")
    resp = client.post(
        "/api/v1/integrations/connections",
        json={
            "provider": "microsoft_graph",
            "name": "tenant-1",
            "config": {"tenant_id": "t", "client_id": "c", "client_secret": "s"},
        },
        headers=headers,
    )
    assert resp.status_code == 402


def test_business_plan_allows_microsoft_graph_integration(client):
    _, headers = bootstrap_tenant(client, slug="bizgraph", plan_code="business")
    resp = client.post(
        "/api/v1/integrations/connections",
        json={
            "provider": "microsoft_graph",
            "name": "tenant-1",
            "config": {"tenant_id": "t", "client_id": "c", "client_secret": "s"},
        },
        headers=headers,
    )
    assert resp.status_code == 201


def test_provider_validates_required_config(client):
    _, headers = bootstrap_tenant(client, slug="bizmissing", plan_code="business")
    resp = client.post(
        "/api/v1/integrations/connections",
        json={"provider": "asana", "name": "default", "config": {}},
        headers=headers,
    )
    # AsanaProvider.required_config_keys = ('personal_access_token', 'workspace_gid')
    assert resp.status_code == 502
    assert "Missing required config" in resp.json()["detail"]


def test_plans_endpoint_lists_seeded_plans(client):
    resp = client.get("/api/v1/subscriptions/plans")
    assert resp.status_code == 200
    codes = {p["code"] for p in resp.json()}
    assert {"free", "starter", "business", "enterprise"}.issubset(codes)
