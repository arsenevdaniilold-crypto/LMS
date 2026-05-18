import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: uuid.UUID
    type: str
    payload: dict[str, Any]
    read: bool
    created_at: datetime


class MarkReadRequest(BaseModel):
    ids: list[uuid.UUID] | None = None
    all: bool = False
