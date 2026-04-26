from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas._common import IDModel, JSONDict, ORMModel


class PlanRead(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    max_users: int | None
    max_contacts: int | None
    max_integrations: int | None
    features: JSONDict
    price_cents: int
    currency: str
    is_active: bool


class SubscriptionAssign(BaseModel):
    plan_code: str = Field(min_length=1, max_length=64)


class SubscriptionRead(IDModel):
    tenant_id: uuid.UUID
    plan_id: uuid.UUID
    plan: PlanRead | None = None
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
