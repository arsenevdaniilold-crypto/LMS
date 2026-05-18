import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import AnnouncementFile
from app.models.class_ import Class, ClassMember
from app.models.solution import Solution, SolutionFile
from app.models.user import RefreshToken, User
from app.services.classes import ClassError


async def list_users(
    db: AsyncSession,
    search: str | None,
    include_deleted: bool,
    page: int,
    page_size: int,
) -> tuple[list[User], int]:
    stmt = select(User)
    if not include_deleted:
        stmt = stmt.where(User.deleted_at.is_(None))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where((User.email.ilike(pattern)) | (User.username.ilike(pattern)))

    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0)
    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    users = list((await db.execute(stmt)).scalars().all())
    return users, total


async def _get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ClassError("USER_NOT_FOUND", "User not found", 404)
    return user


async def block_user(db: AsyncSession, user_id: uuid.UUID, admin: User) -> User:
    user = await _get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise ClassError("CANNOT_BLOCK_SELF", "Admin cannot block themselves", 400)
    if user.deleted_at is not None:
        raise ClassError("ALREADY_BLOCKED", "User is already blocked", 409)

    user.deleted_at = datetime.now(timezone.utc)
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.commit()
    await db.refresh(user)
    return user


async def unblock_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await _get_user_or_404(db, user_id)
    if user.deleted_at is None:
        raise ClassError("NOT_BLOCKED", "User is not blocked", 409)
    user.deleted_at = None
    await db.commit()
    await db.refresh(user)
    return user


async def list_classes(
    db: AsyncSession,
    search: str | None,
    include_deleted: bool,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    stmt = select(Class)
    if not include_deleted:
        stmt = stmt.where(Class.deleted_at.is_(None))
    if search:
        stmt = stmt.where(Class.name.ilike(f"%{search}%"))

    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0)
    stmt = stmt.order_by(Class.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    classes = list((await db.execute(stmt)).scalars().all())

    if not classes:
        return [], total

    creators_result = await db.execute(
        select(User).where(User.id.in_({c.creator_id for c in classes}))
    )
    creators = {u.id: u for u in creators_result.scalars().all()}

    counts_result = await db.execute(
        select(ClassMember.class_id, func.count(ClassMember.id))
        .where(ClassMember.class_id.in_([c.id for c in classes]))
        .group_by(ClassMember.class_id)
    )
    counts = {row[0]: row[1] for row in counts_result.all()}

    items = [
        {
            "id": c.id,
            "name": c.name,
            "type": c.type.value,
            "creator_id": c.creator_id,
            "creator_username": creators[c.creator_id].username if c.creator_id in creators else "",
            "member_count": counts.get(c.id, 0),
            "created_at": c.created_at,
            "deleted_at": c.deleted_at,
        }
        for c in classes
    ]
    return items, total


async def delete_class(db: AsyncSession, class_id: uuid.UUID) -> None:
    result = await db.execute(select(Class).where(Class.id == class_id))
    cls = result.scalar_one_or_none()
    if cls is None:
        raise ClassError("CLASS_NOT_FOUND", "Class not found", 404)
    if cls.deleted_at is not None:
        raise ClassError("ALREADY_DELETED", "Class is already deleted", 409)
    cls.deleted_at = datetime.now(timezone.utc)
    await db.commit()


async def get_stats(db: AsyncSession) -> dict:
    users_total = int((await db.execute(select(func.count(User.id)))).scalar() or 0)
    users_active = int(
        (await db.execute(select(func.count(User.id)).where(User.deleted_at.is_(None)))).scalar() or 0
    )
    classes_total = int((await db.execute(select(func.count(Class.id)))).scalar() or 0)
    classes_active = int(
        (await db.execute(select(func.count(Class.id)).where(Class.deleted_at.is_(None)))).scalar() or 0
    )
    solutions_total = int((await db.execute(select(func.count(Solution.id)))).scalar() or 0)

    ann_bytes = int((await db.execute(select(func.coalesce(func.sum(AnnouncementFile.file_size), 0)))).scalar() or 0)
    sol_bytes = int((await db.execute(select(func.coalesce(func.sum(SolutionFile.file_size), 0)))).scalar() or 0)

    return {
        "users_total": users_total,
        "users_active": users_active,
        "classes_total": classes_total,
        "classes_active": classes_active,
        "solutions_total": solutions_total,
        "file_bytes": ann_bytes + sol_bytes,
    }
