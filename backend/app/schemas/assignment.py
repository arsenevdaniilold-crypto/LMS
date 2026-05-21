import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.enums import AssignmentType, GradeType, GradingType, MaterialType


class AssignmentAuthorResponse(BaseModel):
    id: uuid.UUID
    username: str

    model_config = {"from_attributes": True}


class AssignmentMaterialResponse(BaseModel):
    id: uuid.UUID
    material_type: MaterialType
    url: str | None = None
    file_name: str | None = None
    download_url: str | None = None


class AssignmentResponse(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    name: str
    description: str | None
    type: AssignmentType
    grade_type: GradeType
    grading_type: GradingType | None
    group_count: int | None
    deadline: datetime | None
    author: AssignmentAuthorResponse
    created_at: datetime
    materials: list[AssignmentMaterialResponse]


class AssignmentUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    deadline: datetime | None = None

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2 or len(v) > 255:
            raise ValueError("Name must be 2-255 characters")
        return v


class GroupCreateAutoRequest(BaseModel):
    mode: str = "auto"
    group_count: int

    @field_validator("group_count")
    @classmethod
    def positive(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("group_count must be 1-100")
        return v


class GroupCreateManualRequest(BaseModel):
    mode: str = "manual"
    groups: list[list[uuid.UUID]]

    @field_validator("groups")
    @classmethod
    def non_empty(cls, v: list[list[uuid.UUID]]) -> list[list[uuid.UUID]]:
        if not v:
            raise ValueError("Groups list cannot be empty")
        for group in v:
            if not group:
                raise ValueError("Each group must have at least one member")
        return v


class GroupMemberResponse(BaseModel):
    user_id: uuid.UUID
    username: str


class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    members: list[GroupMemberResponse]
