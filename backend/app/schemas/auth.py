from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterTenantRequest(BaseModel):
    """Bootstrap request creating a tenant + initial admin user atomically."""

    tenant_name: str = Field(min_length=1, max_length=255)
    tenant_slug: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)
    admin_full_name: str = Field(default="", max_length=255)
    plan_code: str = Field(default="free", max_length=64)


class LoginRequest(BaseModel):
    tenant_slug: str = Field(min_length=2, max_length=64)
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
