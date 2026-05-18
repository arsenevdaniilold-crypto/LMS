import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.admin import AdminClassResponse, AdminStatsResponse, AdminUserResponse
from app.services import admin as admin_service
from app.services.classes import ClassError

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _raise(exc: ClassError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


@router.get("/users")
async def list_users(
    search: str | None = Query(default=None, max_length=255),
    include_deleted: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    users, total = await admin_service.list_users(db, search, include_deleted, page, page_size)
    items = [AdminUserResponse.model_validate(u, from_attributes=True) for u in users]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/users/{user_id}/block", response_model=AdminUserResponse)
async def block_user(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await admin_service.block_user(db, user_id, admin)
    except ClassError as exc:
        _raise(exc)
    return AdminUserResponse.model_validate(user, from_attributes=True)


@router.post("/users/{user_id}/unblock", response_model=AdminUserResponse)
async def unblock_user(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await admin_service.unblock_user(db, user_id)
    except ClassError as exc:
        _raise(exc)
    return AdminUserResponse.model_validate(user, from_attributes=True)


@router.get("/classes")
async def list_classes(
    search: str | None = Query(default=None, max_length=255),
    include_deleted: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    items, total = await admin_service.list_classes(db, search, include_deleted, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        await admin_service.delete_class(db, class_id)
    except ClassError as exc:
        _raise(exc)


@router.get("/stats", response_model=AdminStatsResponse)
async def stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.get_stats(db)
