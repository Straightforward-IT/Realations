"""Auth and tenant-isolation tests."""

from __future__ import annotations

from tests.factories import bootstrap_tenant, login, register_tenant


def test_register_and_login_returns_jwt(client):
    user = register_tenant(client, slug="acme")
    assert user["email"] == "admin@acme.example"
    token = login(client, slug="acme", email=user["email"])
    assert token


def test_login_with_wrong_password_returns_401(client):
    register_tenant(client, slug="acme")
    resp = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": "acme", "email": "admin@acme.example", "password": "nope-nope"},
    )
    assert resp.status_code == 401


def test_login_with_unknown_tenant_returns_401(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": "ghosts", "email": "a@b.example", "password": "supersecret123"},
    )
    assert resp.status_code == 401


def test_duplicate_tenant_slug_is_rejected(client):
    register_tenant(client, slug="acme")
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "Acme 2",
            "tenant_slug": "acme",
            "admin_email": "other@acme.example",
            "admin_password": "supersecret123",
            "admin_full_name": "",
            "plan_code": "free",
        },
    )
    assert resp.status_code == 409


def test_tenants_cannot_see_each_others_data(client):
    _, headers_a = bootstrap_tenant(client, slug="alpha")
    _, headers_b = bootstrap_tenant(client, slug="bravo")

    resp = client.post("/api/v1/companies", json={"name": "Alpha Co"}, headers=headers_a)
    assert resp.status_code == 201
    alpha_company_id = resp.json()["id"]

    # Tenant B sees an empty list
    resp = client.get("/api/v1/companies", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json() == []

    # Tenant B cannot read Tenant A's company by direct id either.
    resp = client.get(f"/api/v1/companies/{alpha_company_id}", headers=headers_b)
    assert resp.status_code == 404


def test_request_without_token_is_unauthorized(client):
    resp = client.get("/api/v1/companies")
    assert resp.status_code == 401
