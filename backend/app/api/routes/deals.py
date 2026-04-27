"""Deals CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db, get_license
from app.licensing.checker import LicenseChecker
from app.models.deal import Deal
from app.schemas.deal import DealCreate, DealRead, DealUpdate
from app.services import crud, events

router = APIRouter()


@router.get("", response_model=list[DealRead])
def list_deals(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> list[Deal]:
    return crud.list_for_tenant(session, Deal, tenant_id=current.tenant_id, limit=limit, offset=offset)


@router.post("", response_model=DealRead, status_code=status.HTTP_201_CREATED)
def create_deal(
    payload: DealCreate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Deal:
    obj = crud.create_with_tenant(session, Deal, tenant_id=current.tenant_id, data=payload.model_dump())
    session.commit()
    session.refresh(obj)
    events.publish_event(
        session,
        name="deal.created",
        tenant_id=current.tenant_id,
        payload={"id": str(obj.id), "title": obj.title, "stage": obj.stage},
    )
    return obj


@router.get("/{deal_id}", response_model=DealRead)
def get_deal(
    deal_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Deal:
    return crud.get_for_tenant(session, Deal, tenant_id=current.tenant_id, obj_id=deal_id)


@router.patch("/{deal_id}", response_model=DealRead)
def update_deal(
    deal_id: uuid.UUID,
    payload: DealUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Deal:
    obj = crud.update_for_tenant(
        session,
        Deal,
        tenant_id=current.tenant_id,
        obj_id=deal_id,
        data=payload.model_dump(exclude_unset=True),
    )
    session.commit()
    session.refresh(obj)
    events.publish_event(
        session,
        name="deal.updated",
        tenant_id=current.tenant_id,
        payload={"id": str(obj.id), "stage": obj.stage},
    )
    return obj


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(
    deal_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> None:
    crud.delete_for_tenant(session, Deal, tenant_id=current.tenant_id, obj_id=deal_id)
    session.commit()
    events.publish_event(
        session,
        name="deal.deleted",
        tenant_id=current.tenant_id,
        payload={"id": str(deal_id)},
    )
