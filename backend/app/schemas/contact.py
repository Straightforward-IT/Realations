from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.schemas._common import IDModel, JSONDict


class ContactBase(BaseModel):
    first_name: str = Field(default="", max_length=128)
    last_name: str = Field(default="", max_length=128)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    title: str | None = Field(default=None, max_length=255)
    company_id: uuid.UUID | None = None
    custom_attributes: JSONDict = Field(default_factory=dict)


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=128)
    last_name: str | None = Field(default=None, max_length=128)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    title: str | None = Field(default=None, max_length=255)
    company_id: uuid.UUID | None = None
    custom_attributes: JSONDict | None = None


class ContactRead(IDModel, ContactBase):
    pass
