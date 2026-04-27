"""Webhook endpoint subscriptions + inbound provider receivers."""

from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db, get_license
from app.core.errors import NotFoundError
from app.integrations.base import IntegrationContext, get_provider
from app.licensing.catalog import F_WEBHOOKS
from app.licensing.checker import LicenseChecker
from app.models.integration import IntegrationConnection, WebhookEndpoint
from app.schemas.integration import (
    WebhookEndpointCreate,
    WebhookEndpointRead,
    WebhookEndpointUpdate,
)
from app.services import crud

router = APIRouter()


def _generate_secret() -> str:
    return secrets.token_urlsafe(32)


# ---------------------------------------------------------------------------
# Outbound webhook subscriptions (Zapier-style)
# ---------------------------------------------------------------------------


@router.get("", response_model=list[WebhookEndpointRead])
def list_webhooks(
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> list[WebhookEndpoint]:
    return crud.list_for_tenant(session, WebhookEndpoint, tenant_id=current.tenant_id)


@router.post("", response_model=WebhookEndpointRead, status_code=status.HTTP_201_CREATED)
def create_webhook(
    payload: WebhookEndpointCreate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    license_: LicenseChecker = Depends(get_license),
) -> WebhookEndpoint:
    license_.require_feature(F_WEBHOOKS)
    data = payload.model_dump()
    data["target_url"] = str(data["target_url"])  # cast HttpUrl -> str
    data["secret"] = _generate_secret()
    obj = crud.create_with_tenant(session, WebhookEndpoint, tenant_id=current.tenant_id, data=data)
    session.commit()
    session.refresh(obj)
    return obj


@router.patch("/{webhook_id}", response_model=WebhookEndpointRead)
def update_webhook(
    webhook_id: uuid.UUID,
    payload: WebhookEndpointUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> WebhookEndpoint:
    data = payload.model_dump(exclude_unset=True)
    if "target_url" in data and data["target_url"] is not None:
        data["target_url"] = str(data["target_url"])
    obj = crud.update_for_tenant(
        session, WebhookEndpoint, tenant_id=current.tenant_id, obj_id=webhook_id, data=data
    )
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    webhook_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> None:
    crud.delete_for_tenant(session, WebhookEndpoint, tenant_id=current.tenant_id, obj_id=webhook_id)
    session.commit()


# ---------------------------------------------------------------------------
# Inbound provider receiver
# ---------------------------------------------------------------------------


@router.post("/inbound/{connection_id}")
def inbound_provider_webhook(
    connection_id: uuid.UUID,
    payload: dict = Body(default_factory=dict),
    session: Session = Depends(get_db),
) -> dict:
    """Generic inbound webhook receiver dispatched to the matching provider.

    Authentication on this endpoint is provider-specific (most use HMAC headers
    on the body); we identify the tenant via the connection id in the URL and
    let the provider's ``handle_inbound`` perform any signature checks.
    """
    conn = session.get(IntegrationConnection, connection_id)
    if conn is None or not conn.is_enabled:
        raise NotFoundError("Integration connection not found or disabled")
    provider_cls = get_provider(conn.provider)
    if provider_cls is None:
        raise NotFoundError(f"Unknown provider '{conn.provider}'")
    return provider_cls().handle_inbound(IntegrationContext(session, conn), payload)
