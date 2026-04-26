"""Tickets CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db, get_license
from app.licensing.checker import LicenseChecker
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.services import crud, events

router = APIRouter()


@router.get("", response_model=list[TicketRead])
def list_tickets(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> list[Ticket]:
    return crud.list_for_tenant(
        session, Ticket, tenant_id=current.tenant_id, limit=limit, offset=offset
    )


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Ticket:
    obj = crud.create_with_tenant(
        session, Ticket, tenant_id=current.tenant_id, data=payload.model_dump()
    )
    session.commit()
    session.refresh(obj)
    events.publish_event(
        session,
        name="ticket.created",
        tenant_id=current.tenant_id,
        payload={"id": str(obj.id), "subject": obj.subject},
    )
    return obj


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(
    ticket_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Ticket:
    return crud.get_for_tenant(session, Ticket, tenant_id=current.tenant_id, obj_id=ticket_id)


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Ticket:
    obj = crud.update_for_tenant(
        session,
        Ticket,
        tenant_id=current.tenant_id,
        obj_id=ticket_id,
        data=payload.model_dump(exclude_unset=True),
    )
    session.commit()
    session.refresh(obj)
    events.publish_event(
        session,
        name="ticket.updated",
        tenant_id=current.tenant_id,
        payload={"id": str(obj.id), "status": obj.status},
    )
    return obj


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> None:
    crud.delete_for_tenant(session, Ticket, tenant_id=current.tenant_id, obj_id=ticket_id)
    session.commit()
