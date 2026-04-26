from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas._common import IDModel, JSONDict


class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    custom_attributes: JSONDict = Field(default_factory=dict)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    domain: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    custom_attributes: JSONDict | None = None


class CompanyRead(IDModel, CompanyBase):
    pass
