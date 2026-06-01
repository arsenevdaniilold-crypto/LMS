import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.material import MaterialResponse, MaterialUpdateRequest
from app.services import materials as materials_service
from app.services.classes import ClassError

router = APIRouter(tags=["materials"])


def _raise_class_error(exc: ClassError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


def _validate_title(title: str) -> str:
    title = title.strip()
    if len(title) < 1 or len(title) > 255:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "Title must be 1-255 characters"},
        )
    return title


def _clean_links(links: list[str]) -> list[str]:
    cleaned: list[str] = []
    for raw in links:
        url = raw.strip()
        if not url:
            continue
        if not (url.startswith("http://") or url.startswith("https://")):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "VALIDATION_ERROR", "message": "Links must start with http:// or https://"},
            )
        if len(url) > 2048:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "VALIDATION_ERROR", "message": "Link is too long"},
            )
        cleaned.append(url)
    return cleaned


@router.post(
    "/api/classes/{class_id}/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_material(
    class_id: uuid.UUID,
    title: str = Form(...),
    description: str = Form(default=""),
    links: list[str] = Form(default_factory=list),
    files: list[UploadFile] = File(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    title = _validate_title(title)
    description = description.strip() or None
    clean_links = _clean_links(links)

    uploads: list[tuple[UploadFile, bytes]] = []
    for upload in files:
        data = await upload.read()
        uploads.append((upload, data))

    try:
        return await materials_service.create_material(
            db, class_id, current_user, title, description, uploads, clean_links
        )
    except ClassError as exc:
        _raise_class_error(exc)


@router.get(
    "/api/classes/{class_id}/materials",
    response_model=list[MaterialResponse],
)
async def list_materials(
    class_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await materials_service.list_materials(db, class_id, current_user)
    except ClassError as exc:
        _raise_class_error(exc)


@router.patch(
    "/api/materials/{material_id}",
    response_model=MaterialResponse,
)
async def update_material(
    material_id: uuid.UUID,
    body: MaterialUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    title = body.title
    description = body.description
    if title is not None:
        title = _validate_title(title)
    if description is not None:
        description = description.strip() or None

    try:
        return await materials_service.update_material(
            db, material_id, current_user, title, description
        )
    except ClassError as exc:
        _raise_class_error(exc)


@router.delete(
    "/api/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_material(
    material_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await materials_service.delete_material(db, material_id, current_user)
    except ClassError as exc:
        _raise_class_error(exc)
