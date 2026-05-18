import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import ClassType, MemberRole


class ClassCreateRequest(BaseModel):
    name: str
    type: ClassType

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 255:
            raise ValueError("Name must be 2-255 characters")
        return v


class ClassUpdateRequest(BaseModel):
    name: str | None = None

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2 or len(v) > 255:
            raise ValueError("Name must be 2-255 characters")
        return v


class ClassJoinRequest(BaseModel):
    invite_code: str

    @field_validator("invite_code")
    @classmethod
    def code_format(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 8:
            raise ValueError("Invite code must be 8 characters")
        return v


class InviteTeacherRequest(BaseModel):
    email: EmailStr


class CreatorResponse(BaseModel):
    id: uuid.UUID
    username: str

    model_config = {"from_attributes": True}


class ClassResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: ClassType
    creator_id: uuid.UUID
    creator: CreatorResponse | None = None
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}


class ClassDetailResponse(ClassResponse):
    invite_code: str | None = None
    my_role: MemberRole | None = None


class ClassMemberResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str
    avatar_url: str | None
    role: MemberRole
    joined_at: datetime


class ClassListResponse(BaseModel):
    items: list[ClassResponse]
    total: int
    page: int
    page_size: int


SortBy = Literal["created_desc", "created_asc", "name_asc"]
