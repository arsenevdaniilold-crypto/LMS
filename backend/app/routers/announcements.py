import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.announcement import AnnouncementResponse
from app.services import announcements as announcements_service
from app.services.classes import ClassError

router = APIRouter(tags=["announcements"])


def _raise_class_error(exc: ClassError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


def _validate_title_text(title: str, text: str) -> tuple[str, str]:
    title = title.strip()
    text = text.strip()
    if len(title) < 1 or len(title) > 255:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "Title must be 1-255 characters"},
        )
    if len(text) < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "Text is required"},
        )
    return title, text


@router.post(
    "/api/classes/{class_id}/announcements",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_announcement(
    class_id: uuid.UUID,
    title: str = Form(...),
    text: str = Form(...),
    files: list[UploadFile] = File(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    title, text = _validate_title_text(title, text)

    uploads: list[tuple[UploadFile, bytes]] = []
    for upload in files:
        data = await upload.read()
        uploads.append((upload, data))

    try:
        return await announcements_service.create_announcement(
            db, class_id, current_user, title, text, uploads
        )
    except ClassError as exc:
        _raise_class_error(exc)


@router.get(
    "/api/classes/{class_id}/announcements",
    response_model=list[AnnouncementResponse],
)
async def list_announcements(
    class_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await announcements_service.list_announcements(db, class_id, current_user)
    except ClassError as exc:
        _raise_class_error(exc)


@router.delete(
    "/api/announcements/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_announcement(
    announcement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await announcements_service.delete_announcement(db, announcement_id, current_user)
    except ClassError as exc:
        _raise_class_error(exc)
