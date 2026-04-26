"""Companies CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db, get_license
from app.licensing.checker import LicenseChecker
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.services import crud, events

router = APIRouter()


@router.get("", response_model=list[CompanyRead])
def list_companies(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> list[Company]:
    return crud.list_for_tenant(
        session, Company, tenant_id=current.tenant_id, limit=limit, offset=offset
    )


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Company:
    obj = crud.create_with_tenant(
        session, Company, tenant_id=current.tenant_id, data=payload.model_dump()
    )
    session.commit()
    session.refresh(obj)
    events.publish_event(
        session,
        name="company.created",
        tenant_id=current.tenant_id,
        payload={"id": str(obj.id), "name": obj.name},
    )
    return obj


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Company:
    return crud.get_for_tenant(session, Company, tenant_id=current.tenant_id, obj_id=company_id)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: uuid.UUID,
    payload: CompanyUpdate,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> Company:
    obj = crud.update_for_tenant(
        session,
        Company,
        tenant_id=current.tenant_id,
        obj_id=company_id,
        data=payload.model_dump(exclude_unset=True),
    )
    session.commit()
    session.refresh(obj)
    events.publish_event(
        session,
        name="company.updated",
        tenant_id=current.tenant_id,
        payload={"id": str(obj.id)},
    )
    return obj


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
    _license: LicenseChecker = Depends(get_license),
) -> None:
    crud.delete_for_tenant(session, Company, tenant_id=current.tenant_id, obj_id=company_id)
    session.commit()
    events.publish_event(
        session,
        name="company.deleted",
        tenant_id=current.tenant_id,
        payload={"id": str(company_id)},
    )
