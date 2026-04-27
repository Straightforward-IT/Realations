from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl

from app.schemas._common import IDModel, JSONDict


class IntegrationConnectionBase(BaseModel):
    provider: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    config: JSONDict = Field(default_factory=dict)
    is_enabled: bool = True


class IntegrationConnectionCreate(IntegrationConnectionBase):
    pass


class IntegrationConnectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    config: JSONDict | None = None
    is_enabled: bool | None = None


class IntegrationConnectionRead(IDModel, IntegrationConnectionBase):
    pass


class WebhookEndpointBase(BaseModel):
    target_url: HttpUrl
    event_types: str = Field(default="*", min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class WebhookEndpointCreate(WebhookEndpointBase):
    pass


class WebhookEndpointUpdate(BaseModel):
    target_url: HttpUrl | None = None
    event_types: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class WebhookEndpointRead(IDModel, WebhookEndpointBase):
    target_url: str
    secret: str
