from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas._common import IDModel, JSONDict


class DealBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    stage: str = Field(default="lead", max_length=64)
    amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    currency: str = Field(default="USD", min_length=3, max_length=3)
    company_id: uuid.UUID | None = None
    primary_contact_id: uuid.UUID | None = None
    owner_id: uuid.UUID | None = None
    custom_attributes: JSONDict = Field(default_factory=dict)


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    stage: str | None = Field(default=None, max_length=64)
    amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    company_id: uuid.UUID | None = None
    primary_contact_id: uuid.UUID | None = None
    owner_id: uuid.UUID | None = None
    custom_attributes: JSONDict | None = None


class DealRead(IDModel, DealBase):
    pass
