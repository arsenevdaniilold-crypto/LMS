import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.models.enums import SolutionStatus


class SolutionFileResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    file_size: int
    download_url: str


class SolutionMemberResponse(BaseModel):
    user_id: uuid.UUID
    username: str


class SolutionGroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    members: list[SolutionMemberResponse]


class RedistributionEntryResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    grade: Decimal


class SolutionResponse(BaseModel):
    id: uuid.UUID
    assignment_id: uuid.UUID
    creator_id: uuid.UUID
    creator_username: str
    group: SolutionGroupResponse | None = None
    text: str | None
    status: SolutionStatus
    grade: Decimal | None
    submitted_at: datetime | None
    graded_at: datetime | None
    created_at: datetime
    updated_at: datetime
    files: list[SolutionFileResponse]
    redistribution: list[RedistributionEntryResponse] | None = None


class GradeRequest(BaseModel):
    grade: Decimal

    @field_validator("grade")
    @classmethod
    def non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Grade must be non-negative")
        return v


class RedistributeEntry(BaseModel):
    user_id: uuid.UUID
    grade: Decimal

    @field_validator("grade")
    @classmethod
    def non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Grade must be non-negative")
        return v


class RedistributeRequest(BaseModel):
    grades: list[RedistributeEntry]

    @field_validator("grades")
    @classmethod
    def non_empty(cls, v: list[RedistributeEntry]) -> list[RedistributeEntry]:
        if not v:
            raise ValueError("grades cannot be empty")
        return v


class GradeMatrixCell(BaseModel):
    solution_id: uuid.UUID | None
    status: SolutionStatus | None
    grade: Decimal | None


class GradeMatrixStudent(BaseModel):
    user_id: uuid.UUID
    username: str
    grades: dict[uuid.UUID, GradeMatrixCell]


class GradeMatrixAssignment(BaseModel):
    id: uuid.UUID
    name: str
    grade_type: str
    type: str


class GradesSummaryResponse(BaseModel):
    assignments: list[GradeMatrixAssignment]
    students: list[GradeMatrixStudent]
