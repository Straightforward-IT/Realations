"""Contacts CRUD with license-enforced capacity."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db, get_license
from app.licensing.catalog import F_CUSTOM_FIELDS
from app.licensing.checker import LicenseChecker
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate
from app.services import crud, events

router = APIRouter()


def _maybe_enforce_custom_fields(license_: LicenseChecker, custom_attributes: dict | None) -> None:
    """Reject custom_attributes payloads on plans that don't allow them."""
    if custom_attributes and not license_.has_feature(F_CUSTOM_FIELDS):
        license_.require_feature(F_CUSTOM_FIELDS)


@router.get("", response_model=list[ContactRead])
def list_contacts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> list[Contact]:
    return crud.list_for_tenant(
        session, Contact, tenant_id=current.tenant_id, limit=limit, offset=offset
    )


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    license_: LicenseChecker = Depends(get_license),
) -> Contact:
    license_.require_capacity_for_contact()
    _maybe_enforce_custom_fields(license_, payload.custom_attributes)
    data = payload.model_dump()
    if data.get("email"):
        data["email"] = data["email"].lower()
    obj = crud.create_with_tenant(session, Contact, tenant_id=current.tenant_id, data=data)
    session.commit()
    session.refresh(obj)
    events.publish_event(
        session,
        name="contact.created",
        tenant_id=current.tenant_id,
        payload={"id": str(obj.id), "email": obj.email},
    )
    return obj


@router.get("/{contact_id}", response_model=ContactRead)
def get_contact(
    contact_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Contact:
    return crud.get_for_tenant(session, Contact, tenant_id=current.tenant_id, obj_id=contact_id)


@router.patch("/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    license_: LicenseChecker = Depends(get_license),
) -> Contact:
    data = payload.model_dump(exclude_unset=True)
    _maybe_enforce_custom_fields(license_, data.get("custom_attributes"))
    if data.get("email"):
        data["email"] = data["email"].lower()
    obj = crud.update_for_tenant(
        session, Contact, tenant_id=current.tenant_id, obj_id=contact_id, data=data
    )
    session.commit()
    session.refresh(obj)
    events.publish_event(
        session,
        name="contact.updated",
        tenant_id=current.tenant_id,
        payload={"id": str(obj.id)},
    )
    return obj


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> None:
    crud.delete_for_tenant(session, Contact, tenant_id=current.tenant_id, obj_id=contact_id)
    session.commit()
    events.publish_event(
        session,
        name="contact.deleted",
        tenant_id=current.tenant_id,
        payload={"id": str(contact_id)},
    )
