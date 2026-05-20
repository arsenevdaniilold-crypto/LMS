import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.class_ import (
    ClassCreateRequest,
    ClassDetailResponse,
    ClassJoinRequest,
    ClassListResponse,
    ClassMemberResponse,
    ClassResponse,
    ClassUpdateRequest,
    InviteTeacherRequest,
)
from app.services import classes as classes_service
from app.services.classes import ClassError

router = APIRouter(prefix="/api/classes", tags=["classes"])


def _raise_class_error(exc: ClassError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


@router.post("", response_model=ClassDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    body: ClassCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        cls = await classes_service.create_class(db, current_user, body.name, body.type)
    except ClassError as exc:
        _raise_class_error(exc)
    return await classes_service.get_class_detail(db, cls.id, current_user)


@router.get("", response_model=ClassListResponse)
async def list_open_classes(
    search: str | None = Query(default=None, max_length=255),
    teacher: str | None = Query(default=None, max_length=100),
    sort: Literal["created_desc", "created_asc", "name_asc"] = Query(default="created_desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await classes_service.list_open_classes(
        db, current_user.id, search, teacher, sort, page, page_size
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/my", response_model=list[ClassResponse])
async def list_my_classes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await classes_service.list_my_classes(db, current_user.id)


@router.post("/join", response_model=ClassDetailResponse)
async def join_class(
    body: ClassJoinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await classes_service.join_by_invite_code(db, current_user, body.invite_code)
    except ClassError as exc:
        _raise_class_error(exc)


@router.post("/{class_id}/join", response_model=ClassDetailResponse)
async def join_open_class(
    class_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await classes_service.join_open_class(db, current_user, class_id)
    except ClassError as exc:
        _raise_class_error(exc)


@router.get("/{class_id}", response_model=ClassDetailResponse)
async def get_class(
    class_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await classes_service.get_class_detail(db, class_id, current_user)
    except ClassError as exc:
        _raise_class_error(exc)


@router.patch("/{class_id}", response_model=ClassDetailResponse)
async def update_class(
    class_id: uuid.UUID,
    body: ClassUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await classes_service.update_class(db, class_id, current_user, body.name)
        return await classes_service.get_class_detail(db, class_id, current_user)
    except ClassError as exc:
        _raise_class_error(exc)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await classes_service.delete_class(db, class_id, current_user)
    except ClassError as exc:
        _raise_class_error(exc)


@router.get("/{class_id}/members", response_model=list[ClassMemberResponse])
async def list_members(
    class_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await classes_service.list_members(db, class_id, current_user)
    except ClassError as exc:
        _raise_class_error(exc)


@router.post("/{class_id}/invite-teacher", response_model=ClassMemberResponse)
async def invite_teacher(
    class_id: uuid.UUID,
    body: InviteTeacherRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await classes_service.invite_teacher(db, class_id, current_user, body.email)
    except ClassError as exc:
        _raise_class_error(exc)


@router.delete("/{class_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    class_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await classes_service.remove_member(db, class_id, user_id, current_user)
    except ClassError as exc:
        _raise_class_error(exc)
