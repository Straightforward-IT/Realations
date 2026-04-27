"""Integration connection management.

Exposes:
* ``GET  /providers``                — catalogue of available provider plugins.
* ``GET  /connections``              — list active connections for the tenant.
* ``POST /connections``              — create a new connection (license-gated).
* ``PATCH /connections/{id}``        — update a connection.
* ``DELETE /connections/{id}``       — delete a connection.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db, get_license
from app.core.errors import NotFoundError
from app.integrations.base import get_provider, list_providers
from app.licensing.checker import LicenseChecker
from app.models.integration import IntegrationConnection
from app.schemas.integration import (
    IntegrationConnectionCreate,
    IntegrationConnectionRead,
    IntegrationConnectionUpdate,
)
from app.services import crud

router = APIRouter()


class ProviderInfo(BaseModel):
    slug: str
    display_name: str
    feature_key: str
    required_config_keys: list[str]


@router.get("/providers", response_model=list[ProviderInfo])
def get_providers() -> list[ProviderInfo]:
    return [
        ProviderInfo(
            slug=p.slug,
            display_name=p.display_name,
            feature_key=p.feature_key,
            required_config_keys=list(p.required_config_keys),
        )
        for p in list_providers()
    ]


@router.get("/connections", response_model=list[IntegrationConnectionRead])
def list_connections(
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> list[IntegrationConnection]:
    return crud.list_for_tenant(session, IntegrationConnection, tenant_id=current.tenant_id)


@router.post("/connections", response_model=IntegrationConnectionRead, status_code=status.HTTP_201_CREATED)
def create_connection(
    payload: IntegrationConnectionCreate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    license_: LicenseChecker = Depends(get_license),
) -> IntegrationConnection:
    provider_cls = get_provider(payload.provider)
    if provider_cls is None:
        raise NotFoundError(f"Unknown integration provider '{payload.provider}'")
    license_.require_feature(provider_cls.feature_key)
    license_.require_capacity_for_integration()
    provider_cls.validate_config(payload.config)
    obj = crud.create_with_tenant(
        session, IntegrationConnection, tenant_id=current.tenant_id, data=payload.model_dump()
    )
    session.commit()
    session.refresh(obj)
    return obj


@router.patch("/connections/{connection_id}", response_model=IntegrationConnectionRead)
def update_connection(
    connection_id: uuid.UUID,
    payload: IntegrationConnectionUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> IntegrationConnection:
    existing = crud.get_for_tenant(
        session, IntegrationConnection, tenant_id=current.tenant_id, obj_id=connection_id
    )
    update_data = payload.model_dump(exclude_unset=True)
    if "config" in update_data and update_data["config"] is not None:
        provider_cls = get_provider(existing.provider)
        if provider_cls is not None:
            provider_cls.validate_config(update_data["config"])
    obj = crud.update_for_tenant(
        session,
        IntegrationConnection,
        tenant_id=current.tenant_id,
        obj_id=connection_id,
        data=update_data,
    )
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> None:
    crud.delete_for_tenant(
        session, IntegrationConnection, tenant_id=current.tenant_id, obj_id=connection_id
    )
    session.commit()
