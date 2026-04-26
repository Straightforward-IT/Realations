from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas._common import IDModel, JSONDict


class ActivityBase(BaseModel):
    type: str = Field(min_length=1, max_length=32)
    subject: str = Field(default="", max_length=255)
    body: str | None = None
    occurred_at: datetime | None = None
    contact_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    payload: JSONDict = Field(default_factory=dict)


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    type: str | None = Field(default=None, min_length=1, max_length=32)
    subject: str | None = Field(default=None, max_length=255)
    body: str | None = None
    occurred_at: datetime | None = None
    payload: JSONDict | None = None


class ActivityRead(IDModel, ActivityBase):
    occurred_at: datetime
