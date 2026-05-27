import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest, user_to_response
from app.services.minio_storage import minio_storage

router = APIRouter(prefix="/api/users", tags=["users"])


_AVATAR_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
_AVATAR_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
_AVATAR_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return user_to_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.username is not None:
        current_user.username = body.username
    if body.avatar_url is not None:
        # Manually provided URL (external) is stored as-is.
        current_user.avatar_url = body.avatar_url or None
    await db.commit()
    await db.refresh(current_user)
    return user_to_response(current_user)


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filename = file.filename or "avatar"
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[1].lower()
    if ext not in _AVATAR_ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UNSUPPORTED_FILE_TYPE", "message": "Only .jpg, .jpeg, .png are allowed"},
        )
    if file.content_type and file.content_type not in _AVATAR_ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONTENT_TYPE_MISMATCH", "message": "Image content-type does not match extension"},
        )

    data = await file.read()
    if len(data) > _AVATAR_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "FILE_TOO_LARGE", "message": "Avatar must be up to 5 MB"},
        )

    # Remove old avatar from MinIO if it was uploaded (not external URL)
    old = current_user.avatar_url
    if old and not old.startswith("http"):
        minio_storage.delete(old)

    key = f"avatars/{current_user.id}/{uuid.uuid4()}{ext}"
    minio_storage.upload(key, data, file.content_type or "application/octet-stream")

    current_user.avatar_url = key
    await db.commit()
    await db.refresh(current_user)
    return user_to_response(current_user)


@router.delete("/me/avatar", response_model=UserResponse)
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    old = current_user.avatar_url
    if old and not old.startswith("http"):
        minio_storage.delete(old)
    current_user.avatar_url = None
    await db.commit()
    await db.refresh(current_user)
    return user_to_response(current_user)
