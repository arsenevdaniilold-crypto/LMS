import uuid
from datetime import datetime

from pydantic import BaseModel


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    avatar_url: str | None
    is_admin: bool
    created_at: datetime
    deleted_at: datetime | None


class AdminClassResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    creator_id: uuid.UUID
    creator_username: str
    member_count: int
    created_at: datetime
    deleted_at: datetime | None


class AdminStatsResponse(BaseModel):
    users_total: int
    users_active: int
    classes_total: int
    classes_active: int
    solutions_total: int
    file_bytes: int
