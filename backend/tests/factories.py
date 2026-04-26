"""Reusable factories for tests."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def register_tenant(
    client: TestClient,
    *,
    slug: str,
    name: str | None = None,
    email: str | None = None,
    password: str = "supersecret123",
    plan_code: str = "free",
) -> dict[str, Any]:
    payload = {
        "tenant_name": name or slug.title(),
        "tenant_slug": slug,
        "admin_email": email or f"admin@{slug}.example",
        "admin_password": password,
        "admin_full_name": "Admin",
        "plan_code": plan_code,
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def login(client: TestClient, *, slug: str, email: str, password: str = "supersecret123") -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": slug, "email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def bootstrap_tenant(
    client: TestClient,
    *,
    slug: str,
    plan_code: str = "free",
) -> tuple[str, dict[str, str]]:
    """Register a tenant and return (tenant_id, auth_headers)."""
    user = register_tenant(client, slug=slug, plan_code=plan_code)
    token = login(client, slug=slug, email=user["email"])
    return user["tenant_id"], auth_headers(token)
