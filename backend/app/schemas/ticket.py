from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.schemas._common import IDModel, JSONDict


class TicketBase(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: str = Field(default="open", max_length=32)
    priority: str = Field(default="normal", max_length=16)
    contact_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    assignee_id: uuid.UUID | None = None
    custom_attributes: JSONDict = Field(default_factory=dict)


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(default=None, max_length=32)
    priority: str | None = Field(default=None, max_length=16)
    assignee_id: uuid.UUID | None = None
    custom_attributes: JSONDict | None = None


class TicketRead(IDModel, TicketBase):
    pass
