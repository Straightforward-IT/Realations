"""Shared Pydantic configuration and helpers."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base read-model that hydrates from SQLAlchemy ORM instances."""

    model_config = ConfigDict(from_attributes=True)


class IDModel(ORMModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


JSONDict = dict[str, Any]
