import uuid
from typing import Sequence

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import Announcement, AnnouncementFile
from app.models.class_ import Class
from app.models.enums import MemberRole
from app.models.user import User
from app.services import classes as classes_service
from app.services.classes import ClassError
from app.services.minio_storage import minio_storage
from app.utils.files import validate_upload


async def _ensure_teacher_in_class(db: AsyncSession, class_id: uuid.UUID, user: User) -> Class:
    cls = await classes_service.get_class_or_404(db, class_id)
    membership = await classes_service.get_membership(db, class_id, user.id)
    if membership is None or not classes_service.is_teacher_role(membership.role):
        raise ClassError("FORBIDDEN", "Only teachers can manage announcements", 403)
    return cls


async def _ensure_member(db: AsyncSession, class_id: uuid.UUID, user: User) -> Class:
    cls = await classes_service.get_class_or_404(db, class_id)
    membership = await classes_service.get_membership(db, class_id, user.id)
    if membership is None and not user.is_admin:
        raise ClassError("FORBIDDEN", "You are not a member of this class", 403)
    return cls


def _serialize(announcement: Announcement, files: Sequence[AnnouncementFile], author: User) -> dict:
    return {
        "id": announcement.id,
        "class_id": announcement.class_id,
        "title": announcement.title,
        "text": announcement.text,
        "author": {"id": author.id, "username": author.username},
        "created_at": announcement.created_at,
        "files": [
            {
                "id": f.id,
                "file_name": f.file_name,
                "file_size": f.file_size,
                "download_url": minio_storage.presigned_get_url(f.file_key, f.file_name),
            }
            for f in files
        ],
    }


async def create_announcement(
    db: AsyncSession,
    class_id: uuid.UUID,
    author: User,
    title: str,
    text: str,
    files: list[tuple[UploadFile, bytes]],
) -> dict:
    cls = await _ensure_teacher_in_class(db, class_id, author)

    uploaded_keys: list[str] = []
    file_records: list[tuple[str, str, int]] = []
    try:
        for upload, data in files:
            validate_upload(upload, len(data))
            key = minio_storage.build_key(cls.id, "announcements", upload.filename or "file")
            minio_storage.upload(key, data, upload.content_type or "application/octet-stream")
            uploaded_keys.append(key)
            file_records.append((key, upload.filename or "file", len(data)))

        announcement = Announcement(
            class_id=cls.id,
            author_id=author.id,
            title=title,
            text=text,
        )
        db.add(announcement)
        await db.flush()

        for key, name, size in file_records:
            db.add(AnnouncementFile(
                announcement_id=announcement.id,
                file_key=key,
                file_name=name,
                file_size=size,
            ))
        await db.commit()
        await db.refresh(announcement)
    except Exception:
        await db.rollback()
        for key in uploaded_keys:
            minio_storage.delete(key)
        raise

    files_result = await db.execute(
        select(AnnouncementFile).where(AnnouncementFile.announcement_id == announcement.id)
    )
    return _serialize(announcement, list(files_result.scalars().all()), author)


async def list_announcements(db: AsyncSession, class_id: uuid.UUID, current_user: User) -> list[dict]:
    await _ensure_member(db, class_id, current_user)

    announcements_result = await db.execute(
        select(Announcement)
        .where(Announcement.class_id == class_id)
        .order_by(Announcement.created_at.desc())
    )
    announcements = list(announcements_result.scalars().all())
    if not announcements:
        return []

    ids = [a.id for a in announcements]
    files_result = await db.execute(
        select(AnnouncementFile).where(AnnouncementFile.announcement_id.in_(ids))
    )
    files_by_announcement: dict[uuid.UUID, list[AnnouncementFile]] = {}
    for f in files_result.scalars().all():
        files_by_announcement.setdefault(f.announcement_id, []).append(f)

    author_ids = list({a.author_id for a in announcements})
    authors_result = await db.execute(select(User).where(User.id.in_(author_ids)))
    authors = {u.id: u for u in authors_result.scalars().all()}

    return [
        _serialize(a, files_by_announcement.get(a.id, []), authors[a.author_id])
        for a in announcements
    ]


async def delete_announcement(db: AsyncSession, announcement_id: uuid.UUID, current_user: User) -> None:
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    announcement = result.scalar_one_or_none()
    if announcement is None:
        raise ClassError("ANNOUNCEMENT_NOT_FOUND", "Announcement not found", 404)

    is_author = announcement.author_id == current_user.id
    membership = await classes_service.get_membership(db, announcement.class_id, current_user.id)
    is_teacher = membership is not None and classes_service.is_teacher_role(membership.role)

    if not (is_author or is_teacher):
        raise ClassError("FORBIDDEN", "Only author or teachers can delete the announcement", 403)

    files_result = await db.execute(
        select(AnnouncementFile).where(AnnouncementFile.announcement_id == announcement_id)
    )
    files = list(files_result.scalars().all())

    await db.delete(announcement)
    await db.commit()

    for f in files:
        minio_storage.delete(f.file_key)
