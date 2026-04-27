"""Generic, tenant-scoped CRUD helpers.

These helpers operate on any model that mixes in
:class:`app.db.base.TenantScopedMixin`. They always filter by ``tenant_id``
in addition to the row's primary key, providing defense-in-depth even when
PostgreSQL Row-Level Security is also active.
"""

from __future__ import annotations

import uuid
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.base import Base

T = TypeVar("T", bound=Base)


def create_with_tenant(session: Session, model: type[T], *, tenant_id: uuid.UUID, data: dict[str, Any]) -> T:
    obj = model(tenant_id=tenant_id, **data)
    session.add(obj)
    session.flush()
    return obj


def get_for_tenant(session: Session, model: type[T], *, tenant_id: uuid.UUID, obj_id: uuid.UUID) -> T:
    stmt = select(model).where(model.id == obj_id, model.tenant_id == tenant_id)
    obj = session.execute(stmt).scalar_one_or_none()
    if obj is None:
        raise NotFoundError(f"{model.__name__} {obj_id} not found")
    return obj


def list_for_tenant(
    session: Session,
    model: type[T],
    *,
    tenant_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> list[T]:
    stmt = (
        select(model)
        .where(model.tenant_id == tenant_id)
        .order_by(model.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(session.execute(stmt).scalars())


def update_for_tenant(
    session: Session,
    model: type[T],
    *,
    tenant_id: uuid.UUID,
    obj_id: uuid.UUID,
    data: dict[str, Any],
) -> T:
    obj = get_for_tenant(session, model, tenant_id=tenant_id, obj_id=obj_id)
    for key, value in data.items():
        if value is None:
            continue
        setattr(obj, key, value)
    session.flush()
    return obj


def delete_for_tenant(
    session: Session,
    model: type[T],
    *,
    tenant_id: uuid.UUID,
    obj_id: uuid.UUID,
) -> None:
    obj = get_for_tenant(session, model, tenant_id=tenant_id, obj_id=obj_id)
    session.delete(obj)
    session.flush()
