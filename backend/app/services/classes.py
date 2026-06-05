import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.class_ import Class, ClassMember
from app.models.enums import ClassType, MemberRole
from app.models.user import User
from app.utils.invite import generate_invite_code


MAX_INVITE_CODE_RETRIES = 5


class ClassError(Exception):
    code: str
    message: str
    status_code: int
    details: dict | None

    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


async def _generate_unique_invite_code(db: AsyncSession) -> str:
    for _ in range(MAX_INVITE_CODE_RETRIES):
        code = generate_invite_code()
        exists = await db.execute(select(Class.id).where(Class.invite_code == code))
        if exists.scalar_one_or_none() is None:
            return code
    raise ClassError("INVITE_CODE_GENERATION_FAILED", "Could not generate unique invite code", 500)


async def create_class(db: AsyncSession, creator: User, name: str, class_type: ClassType) -> Class:
    invite_code = await _generate_unique_invite_code(db) if class_type == ClassType.closed else None

    cls = Class(
        name=name,
        type=class_type,
        invite_code=invite_code,
        creator_id=creator.id,
    )
    db.add(cls)
    await db.flush()

    db.add(ClassMember(
        class_id=cls.id,
        user_id=creator.id,
        role=MemberRole.teacher_creator,
    ))
    await db.commit()
    await db.refresh(cls)
    return cls


async def get_class_or_404(db: AsyncSession, class_id: uuid.UUID, include_deleted: bool = False) -> Class:
    stmt = select(Class).where(Class.id == class_id)
    if not include_deleted:
        stmt = stmt.where(Class.deleted_at.is_(None))
    result = await db.execute(stmt)
    cls = result.scalar_one_or_none()
    if cls is None:
        raise ClassError("CLASS_NOT_FOUND", "Class not found", 404)
    return cls


async def get_membership(db: AsyncSession, class_id: uuid.UUID, user_id: uuid.UUID) -> ClassMember | None:
    result = await db.execute(
        select(ClassMember).where(
            ClassMember.class_id == class_id,
            ClassMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


def is_teacher_role(role: MemberRole) -> bool:
    return role in (MemberRole.teacher_creator, MemberRole.teacher)


async def get_member_ids(
    db: AsyncSession,
    class_id: uuid.UUID,
    roles: tuple[MemberRole, ...] | None = None,
) -> list[uuid.UUID]:
    stmt = select(ClassMember.user_id).where(ClassMember.class_id == class_id)
    if roles is not None:
        stmt = stmt.where(ClassMember.role.in_(roles))
    return [row[0] for row in (await db.execute(stmt)).all()]


async def _count_members(db: AsyncSession, class_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count(ClassMember.id)).where(ClassMember.class_id == class_id)
    )
    return int(result.scalar() or 0)


async def _attach_meta(db: AsyncSession, classes: list[Class], current_user_id: uuid.UUID | None = None) -> list[dict]:
    if not classes:
        return []

    class_ids = [c.id for c in classes]
    creator_ids = list({c.creator_id for c in classes})

    creators_result = await db.execute(select(User).where(User.id.in_(creator_ids)))
    creators_by_id = {u.id: u for u in creators_result.scalars().all()}

    counts_result = await db.execute(
        select(ClassMember.class_id, func.count(ClassMember.id))
        .where(ClassMember.class_id.in_(class_ids))
        .group_by(ClassMember.class_id)
    )
    counts_by_class = {row[0]: row[1] for row in counts_result.all()}

    my_roles: dict[uuid.UUID, MemberRole] = {}
    if current_user_id is not None:
        roles_result = await db.execute(
            select(ClassMember.class_id, ClassMember.role).where(
                ClassMember.class_id.in_(class_ids),
                ClassMember.user_id == current_user_id,
            )
        )
        my_roles = {row[0]: row[1] for row in roles_result.all()}

    items: list[dict] = []
    for c in classes:
        items.append({
            "id": c.id,
            "name": c.name,
            "type": c.type,
            "creator_id": c.creator_id,
            "creator": creators_by_id.get(c.creator_id),
            "created_at": c.created_at,
            "member_count": counts_by_class.get(c.id, 0),
            "invite_code": c.invite_code,
            "my_role": my_roles.get(c.id),
        })
    return items


async def list_open_classes(
    db: AsyncSession,
    current_user_id: uuid.UUID,
    search: str | None,
    teacher: str | None,
    sort: str,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    base_stmt = select(Class).where(Class.deleted_at.is_(None), Class.type == ClassType.open)

    if search:
        base_stmt = base_stmt.where(Class.name.ilike(f"%{search}%"))

    if teacher:
        base_stmt = base_stmt.join(User, User.id == Class.creator_id).where(
            User.username.ilike(f"%{teacher}%")
        )

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = int((await db.execute(count_stmt)).scalar() or 0)

    if sort == "created_asc":
        base_stmt = base_stmt.order_by(Class.created_at.asc())
    elif sort == "name_asc":
        base_stmt = base_stmt.order_by(Class.name.asc())
    else:
        base_stmt = base_stmt.order_by(Class.created_at.desc())

    base_stmt = base_stmt.offset((page - 1) * page_size).limit(page_size)
    classes = (await db.execute(base_stmt)).scalars().all()

    items = await _attach_meta(db, list(classes), current_user_id)
    return items, total


async def list_my_classes(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    stmt = (
        select(Class)
        .join(ClassMember, ClassMember.class_id == Class.id)
        .where(
            ClassMember.user_id == user_id,
            Class.deleted_at.is_(None),
        )
        .order_by(Class.created_at.desc())
    )
    classes = (await db.execute(stmt)).scalars().all()
    return await _attach_meta(db, list(classes), user_id)


async def get_class_detail(db: AsyncSession, class_id: uuid.UUID, current_user: User) -> dict:
    cls = await get_class_or_404(db, class_id)
    membership = await get_membership(db, class_id, current_user.id)

    if cls.type == ClassType.closed and membership is None and not current_user.is_admin:
        raise ClassError("FORBIDDEN", "Access to closed class is restricted to members", 403)

    items = await _attach_meta(db, [cls], current_user.id)
    item = items[0]

    if membership is None or not is_teacher_role(membership.role):
        item["invite_code"] = None

    return item


async def regenerate_invite_code(
    db: AsyncSession, class_id: uuid.UUID, current_user: User
) -> dict:
    """Regenerate the invite code for a class.

    Allowed for the class teacher_creator, any class teacher, or admin.
    The old code stops working immediately. For open classes (which don't
    have an invite code) we still issue one — useful for sharing privately.
    """
    cls = await get_class_or_404(db, class_id)
    membership = await get_membership(db, class_id, current_user.id)
    is_teacher = membership is not None and is_teacher_role(membership.role)
    if not (is_teacher or current_user.is_admin):
        raise ClassError(
            "FORBIDDEN", "Only teachers or admin can regenerate invite code", 403
        )

    cls.invite_code = await _generate_unique_invite_code(db)
    await db.commit()
    await db.refresh(cls)

    items = await _attach_meta(db, [cls], current_user.id)
    return items[0]


async def update_class(db: AsyncSession, class_id: uuid.UUID, current_user: User, name: str | None) -> dict:
    cls = await get_class_or_404(db, class_id)
    membership = await get_membership(db, class_id, current_user.id)
    if membership is None or not is_teacher_role(membership.role):
        raise ClassError("FORBIDDEN", "Only teachers can update class", 403)

    if name is not None:
        cls.name = name
        await db.commit()
        await db.refresh(cls)

    items = await _attach_meta(db, [cls], current_user.id)
    return items[0]


async def delete_class(db: AsyncSession, class_id: uuid.UUID, current_user: User) -> None:
    cls = await get_class_or_404(db, class_id)
    membership = await get_membership(db, class_id, current_user.id)
    if membership is None or membership.role != MemberRole.teacher_creator:
        raise ClassError("FORBIDDEN", "Only class creator can delete class", 403)

    cls.deleted_at = datetime.now(timezone.utc)
    await db.commit()


async def _join_as_student(db: AsyncSession, cls: Class, current_user: User) -> dict:
    existing = await get_membership(db, cls.id, current_user.id)
    if existing is not None:
        raise ClassError("ALREADY_MEMBER", "You are already a member of this class", 409)

    db.add(ClassMember(
        class_id=cls.id,
        user_id=current_user.id,
        role=MemberRole.student,
    ))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ClassError("ALREADY_MEMBER", "You are already a member of this class", 409)

    items = await _attach_meta(db, [cls], current_user.id)
    return items[0]


async def join_by_invite_code(db: AsyncSession, current_user: User, invite_code: str) -> dict:
    result = await db.execute(
        select(Class).where(
            Class.invite_code == invite_code,
            Class.deleted_at.is_(None),
        )
    )
    cls = result.scalar_one_or_none()
    if cls is None:
        raise ClassError("INVALID_INVITE_CODE", "Invalid invite code", 404)
    return await _join_as_student(db, cls, current_user)


async def join_open_class(db: AsyncSession, current_user: User, class_id: uuid.UUID) -> dict:
    cls = await get_class_or_404(db, class_id)
    if cls.type != ClassType.open:
        raise ClassError("NOT_OPEN_CLASS", "Only open classes can be joined by id", 403)
    return await _join_as_student(db, cls, current_user)


async def list_members(db: AsyncSession, class_id: uuid.UUID, current_user: User) -> list[dict]:
    cls = await get_class_or_404(db, class_id)
    membership = await get_membership(db, class_id, current_user.id)
    if membership is None and not current_user.is_admin:
        raise ClassError("FORBIDDEN", "You are not a member of this class", 403)

    stmt = (
        select(ClassMember, User)
        .join(User, User.id == ClassMember.user_id)
        .where(ClassMember.class_id == class_id)
        .order_by(ClassMember.joined_at.asc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "role": member.role,
            "joined_at": member.joined_at,
        }
        for member, user in rows
    ]


async def invite_teacher(db: AsyncSession, class_id: uuid.UUID, current_user: User, email: str) -> dict:
    cls = await get_class_or_404(db, class_id)
    current_membership = await get_membership(db, class_id, current_user.id)
    if current_membership is None or not is_teacher_role(current_membership.role):
        raise ClassError("FORBIDDEN", "Only teachers can invite teachers", 403)

    user_result = await db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )
    target = user_result.scalar_one_or_none()
    if target is None:
        raise ClassError("USER_NOT_FOUND", "User with this email not found", 404)

    target_membership = await get_membership(db, class_id, target.id)
    if target_membership is None:
        raise ClassError("NOT_A_MEMBER", "User must be a member of the class first", 404)

    if target_membership.role == MemberRole.teacher_creator:
        raise ClassError("ALREADY_CREATOR", "User is already the class creator", 409)

    if target_membership.role == MemberRole.teacher:
        raise ClassError("ALREADY_TEACHER", "User is already a teacher", 409)

    target_membership.role = MemberRole.teacher
    await db.commit()

    return {
        "user_id": target.id,
        "username": target.username,
        "email": target.email,
        "avatar_url": target.avatar_url,
        "role": target_membership.role,
        "joined_at": target_membership.joined_at,
    }


async def promote_member_to_teacher(
    db: AsyncSession,
    class_id: uuid.UUID,
    target_user_id: uuid.UUID,
    current_user: User,
) -> dict:
    """Promote a class member (currently student) to teacher.

    Allowed for class creator or admin. Already-teacher targets are no-ops
    that surface as `ALREADY_TEACHER`.
    """
    await get_class_or_404(db, class_id)
    current_membership = await get_membership(db, class_id, current_user.id)
    is_creator = (
        current_membership is not None
        and current_membership.role == MemberRole.teacher_creator
    )
    if not (is_creator or current_user.is_admin):
        raise ClassError(
            "FORBIDDEN", "Only class creator or admin can change member roles", 403
        )

    target_membership = await get_membership(db, class_id, target_user_id)
    if target_membership is None:
        raise ClassError("MEMBER_NOT_FOUND", "User is not a member of this class", 404)
    if target_membership.role == MemberRole.teacher_creator:
        raise ClassError("ALREADY_CREATOR", "User is the class creator", 409)
    if target_membership.role == MemberRole.teacher:
        raise ClassError("ALREADY_TEACHER", "User is already a teacher", 409)

    target_membership.role = MemberRole.teacher
    await db.commit()

    user = (await db.execute(select(User).where(User.id == target_user_id))).scalar_one()
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "role": target_membership.role,
        "joined_at": target_membership.joined_at,
    }


async def demote_member_to_student(
    db: AsyncSession,
    class_id: uuid.UUID,
    target_user_id: uuid.UUID,
    current_user: User,
    new_creator_id: uuid.UUID | None = None,
) -> dict:
    """Demote a class teacher (or creator) down to student.

    Cases:
      * target is a regular teacher → just flip role (creator and admin both
        allowed).
      * target is teacher_creator → only admin may do this and must pass
        ``new_creator_id`` pointing at another teacher_creator/teacher member
        (students are not allowed as new creators).
    """
    cls = await get_class_or_404(db, class_id)
    current_membership = await get_membership(db, class_id, current_user.id)
    is_creator = (
        current_membership is not None
        and current_membership.role == MemberRole.teacher_creator
    )
    if not (is_creator or current_user.is_admin):
        raise ClassError(
            "FORBIDDEN", "Only class creator or admin can change member roles", 403
        )

    target_membership = await get_membership(db, class_id, target_user_id)
    if target_membership is None:
        raise ClassError("MEMBER_NOT_FOUND", "User is not a member of this class", 404)
    if target_membership.role == MemberRole.student:
        raise ClassError("ALREADY_STUDENT", "User is already a student", 409)

    if target_membership.role == MemberRole.teacher_creator:
        # Demoting the creator means transferring ownership.
        if not current_user.is_admin:
            raise ClassError(
                "FORBIDDEN", "Only admin can demote the class creator", 403
            )
        if new_creator_id is None:
            raise ClassError(
                "NEW_CREATOR_REQUIRED",
                "new_creator_id is required when demoting the class creator",
                422,
            )
        if new_creator_id == target_user_id:
            raise ClassError(
                "NEW_CREATOR_REQUIRED",
                "new_creator must be a different user",
                422,
            )
        new_creator_membership = await get_membership(db, class_id, new_creator_id)
        if new_creator_membership is None:
            raise ClassError(
                "NEW_CREATOR_NOT_IN_CLASS",
                "New creator must be a member of this class",
                404,
            )
        if new_creator_membership.role == MemberRole.student:
            raise ClassError(
                "NEW_CREATOR_NOT_TEACHER",
                "Cannot promote a student to creator — pick a teacher",
                422,
            )
        new_creator_membership.role = MemberRole.teacher_creator
        cls.creator_id = new_creator_id

    target_membership.role = MemberRole.student
    await db.commit()

    user = (await db.execute(select(User).where(User.id == target_user_id))).scalar_one()
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "role": target_membership.role,
        "joined_at": target_membership.joined_at,
    }


async def remove_member(db: AsyncSession, class_id: uuid.UUID, target_user_id: uuid.UUID, current_user: User) -> None:
    cls = await get_class_or_404(db, class_id)
    current_membership = await get_membership(db, class_id, current_user.id)
    if current_membership is None or not is_teacher_role(current_membership.role):
        raise ClassError("FORBIDDEN", "Only teachers can remove members", 403)

    target_membership = await get_membership(db, class_id, target_user_id)
    if target_membership is None:
        raise ClassError("MEMBER_NOT_FOUND", "User is not a member of this class", 404)

    if target_membership.role == MemberRole.teacher_creator:
        raise ClassError("CANNOT_REMOVE_CREATOR", "Cannot remove class creator", 403)

    if target_membership.role == MemberRole.teacher and current_membership.role != MemberRole.teacher_creator:
        raise ClassError("FORBIDDEN", "Only class creator can remove teachers", 403)

    await db.delete(target_membership)
    await db.commit()
