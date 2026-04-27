"""Activity log endpoints (append-mostly)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db, get_license
from app.licensing.checker import LicenseChecker
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.services import crud, events

router = APIRouter()


@router.get("", response_model=list[ActivityRead])
def list_activities(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> list[Activity]:
    return crud.list_for_tenant(
        session, Activity, tenant_id=current.tenant_id, limit=limit, offset=offset
    )


@router.post("", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    payload: ActivityCreate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Activity:
    data = payload.model_dump()
    if data.get("occurred_at") is None:
        data["occurred_at"] = datetime.now(UTC)
    obj = crud.create_with_tenant(session, Activity, tenant_id=current.tenant_id, data=data)
    session.commit()
    session.refresh(obj)
    events.publish_event(
        session,
        name="activity.created",
        tenant_id=current.tenant_id,
        payload={"id": str(obj.id), "type": obj.type},
    )
    return obj


@router.get("/{activity_id}", response_model=ActivityRead)
def get_activity(
    activity_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Activity:
    return crud.get_for_tenant(session, Activity, tenant_id=current.tenant_id, obj_id=activity_id)


@router.patch("/{activity_id}", response_model=ActivityRead)
def update_activity(
    activity_id: uuid.UUID,
    payload: ActivityUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Activity:
    obj = crud.update_for_tenant(
        session,
        Activity,
        tenant_id=current.tenant_id,
        obj_id=activity_id,
        data=payload.model_dump(exclude_unset=True),
    )
    session.commit()
    session.refresh(obj)
    return obj


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> None:
    crud.delete_for_tenant(session, Activity, tenant_id=current.tenant_id, obj_id=activity_id)
    session.commit()
