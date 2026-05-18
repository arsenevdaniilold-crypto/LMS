import uuid
from datetime import datetime

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.enums import AssignmentType, GradeType, GradingType
from app.models.user import User
from app.schemas.assignment import (
    AssignmentResponse,
    AssignmentUpdateRequest,
    GroupCreateAutoRequest,
    GroupCreateManualRequest,
    GroupResponse,
)
from app.services import assignments as assignments_service
from app.services.classes import ClassError

router = APIRouter(tags=["assignments"])


def _raise(exc: ClassError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


def _validate_name(name: str) -> str:
    name = name.strip()
    if len(name) < 2 or len(name) > 255:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "Name must be 2-255 characters"},
        )
    return name


@router.post(
    "/api/classes/{class_id}/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment(
    class_id: uuid.UUID,
    name: str = Form(...),
    description: str | None = Form(default=None),
    type: AssignmentType = Form(...),
    grade_type: GradeType = Form(...),
    grading_type: GradingType | None = Form(default=None),
    group_count: int | None = Form(default=None),
    deadline: datetime | None = Form(default=None),
    files: list[UploadFile] = File(default_factory=list),
    links: list[str] = Form(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    name = _validate_name(name)
    uploads: list[tuple[UploadFile, bytes]] = []
    for upload in files:
        data = await upload.read()
        uploads.append((upload, data))

    try:
        return await assignments_service.create_assignment(
            db, class_id, current_user, name, description,
            type, grade_type, grading_type, group_count, deadline,
            uploads, links,
        )
    except ClassError as exc:
        _raise(exc)


@router.get(
    "/api/classes/{class_id}/assignments",
    response_model=list[AssignmentResponse],
)
async def list_assignments(
    class_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await assignments_service.list_assignments(db, class_id, current_user)
    except ClassError as exc:
        _raise(exc)


@router.get(
    "/api/assignments/{assignment_id}",
    response_model=AssignmentResponse,
)
async def get_assignment(
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await assignments_service.get_assignment_detail(db, assignment_id, current_user)
    except ClassError as exc:
        _raise(exc)


@router.patch(
    "/api/assignments/{assignment_id}",
    response_model=AssignmentResponse,
)
async def update_assignment(
    assignment_id: uuid.UUID,
    body: AssignmentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await assignments_service.update_assignment(
            db, assignment_id, current_user, body.name, body.description, body.deadline
        )
    except ClassError as exc:
        _raise(exc)


@router.delete(
    "/api/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_assignment(
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await assignments_service.delete_assignment(db, assignment_id, current_user)
    except ClassError as exc:
        _raise(exc)


@router.post(
    "/api/assignments/{assignment_id}/groups",
    response_model=list[GroupResponse],
)
async def create_groups(
    assignment_id: uuid.UUID,
    body: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mode = body.get("mode")
    try:
        if mode == "auto":
            req = GroupCreateAutoRequest(**body)
            return await assignments_service.create_groups_auto(
                db, assignment_id, current_user, req.group_count
            )
        elif mode == "manual":
            req = GroupCreateManualRequest(**body)
            return await assignments_service.create_groups_manual(
                db, assignment_id, current_user, req.groups
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "VALIDATION_ERROR", "message": "mode must be 'auto' or 'manual'"},
            )
    except ClassError as exc:
        _raise(exc)


@router.get(
    "/api/assignments/{assignment_id}/groups",
    response_model=list[GroupResponse],
)
async def list_groups(
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await assignments_service.list_groups(db, assignment_id, current_user)
    except ClassError as exc:
        _raise(exc)
