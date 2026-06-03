import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import Announcement, AnnouncementFile
from app.models.assignment import Assignment
from app.models.class_ import Class, ClassMember
from app.models.enums import MemberRole
from app.models.solution import GradeRedistribution, Solution, SolutionFile
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


async def transfer_class(
    db: AsyncSession,
    class_id: uuid.UUID,
    new_creator_id: uuid.UUID,
) -> Class:
    """Reassign a class to a different creator.

    The previous creator stays in the class as a teacher (if they were a
    member); the new creator becomes the teacher_creator. The new creator must
    be an existing active user.
    """
    cls = (await db.execute(select(Class).where(Class.id == class_id))).scalar_one_or_none()
    if cls is None:
        raise ClassError("CLASS_NOT_FOUND", "Class not found", 404)

    if cls.creator_id == new_creator_id:
        raise ClassError("SAME_CREATOR", "Class is already owned by this user", 400)

    new_creator = (
        await db.execute(select(User).where(User.id == new_creator_id, User.deleted_at.is_(None)))
    ).scalar_one_or_none()
    if new_creator is None:
        raise ClassError("USER_NOT_FOUND", "New creator must be an active user", 404)

    old_creator_id = cls.creator_id
    cls.creator_id = new_creator_id

    # Downgrade the previous creator's membership to teacher (if they had one).
    old_membership = (await db.execute(
        select(ClassMember).where(
            ClassMember.class_id == class_id,
            ClassMember.user_id == old_creator_id,
        )
    )).scalar_one_or_none()
    if old_membership is not None and old_membership.role == MemberRole.teacher_creator:
        old_membership.role = MemberRole.teacher

    # Upsert the new creator's membership as teacher_creator.
    new_membership = (await db.execute(
        select(ClassMember).where(
            ClassMember.class_id == class_id,
            ClassMember.user_id == new_creator_id,
        )
    )).scalar_one_or_none()
    if new_membership is None:
        new_membership = ClassMember(
            class_id=class_id,
            user_id=new_creator_id,
            role=MemberRole.teacher_creator,
        )
        db.add(new_membership)
    else:
        new_membership.role = MemberRole.teacher_creator

    await db.commit()
    await db.refresh(cls)
    return cls


async def delete_user(
    db: AsyncSession, user_id: uuid.UUID, admin: User, *, force: bool = False
) -> None:
    """Physically remove a user from the database.

    By default refuses with 409 USER_HAS_CONTENT if the user still owns
    *active* classes/announcements/assignments/solutions (admin transfers or
    deletes them first via the modal).

    With ``force=True`` the admin explicitly chose to wipe everything: all of
    the user's content (solutions, announcements, assignments + cascades) and
    classes are physically removed, then the user.

    Soft-deleted classes the user created are always swept (they were already
    gone from the user's view but still held a FK).
    """
    user = await _get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise ClassError("CANNOT_DELETE_SELF", "Admin cannot delete themselves", 400)
    if user.is_admin:
        raise ClassError("CANNOT_DELETE_ADMIN", "Admins cannot be deleted; remove admin rights first", 400)

    if not force:
        # Active conflicts — these block the delete and require admin action.
        owned_active_classes = list((await db.execute(
            select(Class.id, Class.name).where(
                Class.creator_id == user.id, Class.deleted_at.is_(None),
            )
        )).all())
        ann_count = int((await db.execute(
            select(func.count(Announcement.id)).where(Announcement.author_id == user.id)
        )).scalar() or 0)
        asn_count = int((await db.execute(
            select(func.count(Assignment.id)).where(Assignment.author_id == user.id)
        )).scalar() or 0)
        sol_count = int((await db.execute(
            select(func.count(Solution.id)).where(Solution.creator_id == user.id)
        )).scalar() or 0)

        if owned_active_classes or ann_count or asn_count or sol_count:
            raise ClassError(
                "USER_HAS_CONTENT",
                "User still owns content. Transfer or delete it first.",
                409,
                details={
                    "classes_owned": [
                        {"id": str(c.id), "name": c.name} for c in owned_active_classes
                    ],
                    "announcements": ann_count,
                    "assignments": asn_count,
                    "solutions": sol_count,
                },
            )

    if force:
        # Wipe all content the user owns. Order matters because several FKs
        # don't cascade from users.
        # 1. The user's rows inside *other* solutions' redistribution tables.
        await db.execute(
            delete(GradeRedistribution).where(GradeRedistribution.user_id == user.id)
        )
        # 2. The user's own solutions (cascades: solution_files, their redistributions).
        await db.execute(delete(Solution).where(Solution.creator_id == user.id))
        # 3. The user's announcements (cascades: announcement_files).
        await db.execute(delete(Announcement).where(Announcement.author_id == user.id))
        # 4. The user's assignments (cascades: materials, groups→group_members,
        #    other students' solutions on these assignments).
        await db.execute(delete(Assignment).where(Assignment.author_id == user.id))
        await db.flush()

    # Sweep classes the user created (active + soft-deleted). Cascading FKs
    # (class_members, announcements, assignments) clean up their content.
    owned_classes = list((await db.execute(
        select(Class).where(Class.creator_id == user.id)
    )).scalars().all())
    for cls in owned_classes:
        await db.delete(cls)
    if owned_classes:
        await db.flush()

    # Safe to hard-delete: cascades take care of class_members, notifications,
    # group_members, refresh_tokens.
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.delete(user)
    await db.commit()


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
