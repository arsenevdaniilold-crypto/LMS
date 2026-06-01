import uuid
from typing import Sequence

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.enums import MaterialType
from app.models.material import Material, MaterialItem
from app.models.user import User
from app.services import classes as classes_service
from app.services import notifications as notifications_service
from app.services.classes import ClassError
from app.services.minio_storage import minio_storage
from app.utils.files import validate_upload


async def _ensure_teacher_in_class(db: AsyncSession, class_id: uuid.UUID, user: User) -> Class:
    cls = await classes_service.get_class_or_404(db, class_id)
    membership = await classes_service.get_membership(db, class_id, user.id)
    if membership is None or not classes_service.is_teacher_role(membership.role):
        raise ClassError("FORBIDDEN", "Only teachers can manage materials", 403)
    return cls


async def _ensure_member(db: AsyncSession, class_id: uuid.UUID, user: User) -> Class:
    cls = await classes_service.get_class_or_404(db, class_id)
    membership = await classes_service.get_membership(db, class_id, user.id)
    if membership is None and not user.is_admin:
        raise ClassError("FORBIDDEN", "You are not a member of this class", 403)
    return cls


def _serialize(material: Material, items: Sequence[MaterialItem], author: User) -> dict:
    return {
        "id": material.id,
        "class_id": material.class_id,
        "title": material.title,
        "description": material.description,
        "author": {"id": author.id, "username": author.username},
        "created_at": material.created_at,
        "items": [
            {
                "id": it.id,
                "item_type": it.item_type,
                "url": it.url,
                "file_name": it.file_name,
                "file_size": it.file_size,
                "download_url": (
                    minio_storage.presigned_get_url(it.file_key, it.file_name)
                    if it.item_type == MaterialType.file and it.file_key
                    else None
                ),
            }
            for it in items
        ],
    }


async def create_material(
    db: AsyncSession,
    class_id: uuid.UUID,
    author: User,
    title: str,
    description: str | None,
    files: list[tuple[UploadFile, bytes]],
    links: list[str],
) -> dict:
    cls = await _ensure_teacher_in_class(db, class_id, author)

    if not files and not links:
        raise ClassError("VALIDATION_ERROR", "Add at least one file or link", 422)

    uploaded_keys: list[str] = []
    file_records: list[tuple[str, str, int]] = []
    try:
        for upload, data in files:
            validate_upload(upload, len(data))
            key = minio_storage.build_key(cls.id, "materials", upload.filename or "file")
            minio_storage.upload(key, data, upload.content_type or "application/octet-stream")
            uploaded_keys.append(key)
            file_records.append((key, upload.filename or "file", len(data)))

        material = Material(
            class_id=cls.id,
            author_id=author.id,
            title=title,
            description=description,
        )
        db.add(material)
        await db.flush()

        for key, name, size in file_records:
            db.add(MaterialItem(
                material_id=material.id,
                item_type=MaterialType.file,
                file_key=key,
                file_name=name,
                file_size=size,
            ))
        for url in links:
            db.add(MaterialItem(
                material_id=material.id,
                item_type=MaterialType.link,
                url=url,
            ))
        await db.commit()
        await db.refresh(material)
    except Exception:
        await db.rollback()
        for key in uploaded_keys:
            minio_storage.delete(key)
        raise

    items_result = await db.execute(
        select(MaterialItem).where(MaterialItem.material_id == material.id)
    )

    member_ids = await classes_service.get_member_ids(db, cls.id)
    recipients = [uid for uid in member_ids if uid != author.id]
    await notifications_service.notify(
        db,
        recipients,
        "material_created",
        {
            "class_id": str(cls.id),
            "class_name": cls.name,
            "material_id": str(material.id),
            "title": material.title,
            "author_username": author.username,
        },
    )
    await db.commit()

    return _serialize(material, list(items_result.scalars().all()), author)


async def list_materials(db: AsyncSession, class_id: uuid.UUID, current_user: User) -> list[dict]:
    await _ensure_member(db, class_id, current_user)

    materials_result = await db.execute(
        select(Material)
        .where(Material.class_id == class_id)
        .order_by(Material.created_at.desc())
    )
    materials = list(materials_result.scalars().all())
    if not materials:
        return []

    ids = [m.id for m in materials]
    items_result = await db.execute(
        select(MaterialItem).where(MaterialItem.material_id.in_(ids))
    )
    items_by_material: dict[uuid.UUID, list[MaterialItem]] = {}
    for it in items_result.scalars().all():
        items_by_material.setdefault(it.material_id, []).append(it)

    author_ids = list({m.author_id for m in materials})
    authors_result = await db.execute(select(User).where(User.id.in_(author_ids)))
    authors = {u.id: u for u in authors_result.scalars().all()}

    return [
        _serialize(m, items_by_material.get(m.id, []), authors[m.author_id])
        for m in materials
    ]


async def update_material(
    db: AsyncSession,
    material_id: uuid.UUID,
    current_user: User,
    title: str | None,
    description: str | None,
) -> dict:
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if material is None:
        raise ClassError("MATERIAL_NOT_FOUND", "Material not found", 404)

    is_author = material.author_id == current_user.id
    membership = await classes_service.get_membership(db, material.class_id, current_user.id)
    is_teacher = membership is not None and classes_service.is_teacher_role(membership.role)
    if not (is_author or is_teacher):
        raise ClassError("FORBIDDEN", "Only author or teachers can edit the material", 403)

    if title is not None:
        material.title = title
    if description is not None:
        material.description = description
    await db.flush()

    cls = await classes_service.get_class_or_404(db, material.class_id)
    member_ids = await classes_service.get_member_ids(db, material.class_id)
    recipients = [uid for uid in member_ids if uid != current_user.id]
    await notifications_service.notify(
        db,
        recipients,
        "material_updated",
        {
            "class_id": str(material.class_id),
            "class_name": cls.name,
            "material_id": str(material.id),
            "title": material.title,
        },
    )
    await db.commit()
    await db.refresh(material)

    items_result = await db.execute(
        select(MaterialItem).where(MaterialItem.material_id == material.id)
    )
    author_result = await db.execute(select(User).where(User.id == material.author_id))
    author = author_result.scalar_one()
    return _serialize(material, list(items_result.scalars().all()), author)


async def delete_material(db: AsyncSession, material_id: uuid.UUID, current_user: User) -> None:
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if material is None:
        raise ClassError("MATERIAL_NOT_FOUND", "Material not found", 404)

    is_author = material.author_id == current_user.id
    membership = await classes_service.get_membership(db, material.class_id, current_user.id)
    is_teacher = membership is not None and classes_service.is_teacher_role(membership.role)

    if not (is_author or is_teacher or current_user.is_admin):
        raise ClassError("FORBIDDEN", "Only author or teachers can delete the material", 403)

    items_result = await db.execute(
        select(MaterialItem).where(MaterialItem.material_id == material_id)
    )
    items = list(items_result.scalars().all())

    class_id = material.class_id
    cls = await classes_service.get_class_or_404(db, class_id)
    member_ids = await classes_service.get_member_ids(db, class_id)
    recipients = [uid for uid in member_ids if uid != current_user.id]

    await db.delete(material)
    await notifications_service.notify(
        db,
        recipients,
        "material_deleted",
        {
            "class_id": str(class_id),
            "class_name": cls.name,
            "material_id": str(material_id),
        },
    )
    await db.commit()

    for it in items:
        if it.file_key:
            minio_storage.delete(it.file_key)
