import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.solution import (
    GradeRequest,
    GradesSummaryResponse,
    RedistributeRequest,
    SolutionResponse,
)
from app.services import grades as grades_service
from app.services import solutions as solutions_service
from app.services.classes import ClassError

router = APIRouter(tags=["solutions"])


def _raise(exc: ClassError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


async def _read_uploads(files: list[UploadFile]) -> list[tuple[UploadFile, bytes]]:
    out: list[tuple[UploadFile, bytes]] = []
    for upload in files:
        data = await upload.read()
        out.append((upload, data))
    return out


@router.post(
    "/api/assignments/{assignment_id}/solutions",
    response_model=SolutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_solution(
    assignment_id: uuid.UUID,
    text: str | None = Form(default=None),
    files: list[UploadFile] = File(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uploads = await _read_uploads(files)
    try:
        return await solutions_service.create_solution(
            db, assignment_id, current_user, text, uploads
        )
    except ClassError as exc:
        _raise(exc)


@router.patch(
    "/api/solutions/{solution_id}",
    response_model=SolutionResponse,
)
async def update_solution(
    solution_id: uuid.UUID,
    text: str | None = Form(default=None),
    files: list[UploadFile] = File(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uploads = await _read_uploads(files)
    try:
        return await solutions_service.update_solution(
            db, solution_id, current_user, text, uploads
        )
    except ClassError as exc:
        _raise(exc)


@router.get(
    "/api/assignments/{assignment_id}/solutions",
    response_model=list[SolutionResponse],
)
async def list_solutions(
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await solutions_service.list_solutions(db, assignment_id, current_user)
    except ClassError as exc:
        _raise(exc)


@router.get(
    "/api/solutions/{solution_id}",
    response_model=SolutionResponse,
)
async def get_solution(
    solution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await solutions_service.get_solution_detail(db, solution_id, current_user)
    except ClassError as exc:
        _raise(exc)


@router.post(
    "/api/solutions/{solution_id}/submit",
    response_model=SolutionResponse,
)
async def submit_solution(
    solution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await solutions_service.submit_solution(db, solution_id, current_user)
    except ClassError as exc:
        _raise(exc)


@router.post(
    "/api/solutions/{solution_id}/return",
    response_model=SolutionResponse,
)
async def return_solution(
    solution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await solutions_service.return_solution(db, solution_id, current_user)
    except ClassError as exc:
        _raise(exc)


@router.post(
    "/api/solutions/{solution_id}/grade",
    response_model=SolutionResponse,
)
async def grade_solution(
    solution_id: uuid.UUID,
    body: GradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await solutions_service.grade_solution(
            db, solution_id, current_user, body.grade
        )
    except ClassError as exc:
        _raise(exc)


@router.post(
    "/api/solutions/{solution_id}/redistribute",
    response_model=SolutionResponse,
)
async def redistribute_solution(
    solution_id: uuid.UUID,
    body: RedistributeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        entries = [(e.user_id, e.grade) for e in body.grades]
        return await solutions_service.redistribute_solution(
            db, solution_id, current_user, entries
        )
    except ClassError as exc:
        _raise(exc)


@router.get(
    "/api/classes/{class_id}/grades",
    response_model=GradesSummaryResponse,
)
async def class_grades(
    class_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await grades_service.get_class_grades(db, class_id, current_user)
    except ClassError as exc:
        _raise(exc)
