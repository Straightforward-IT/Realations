from __future__ import annotations

import uuid

from pydantic import EmailStr

from app.schemas._common import IDModel


class UserRead(IDModel):
    tenant_id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
