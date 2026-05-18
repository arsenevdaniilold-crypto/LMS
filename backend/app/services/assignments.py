import random
import uuid
from datetime import datetime
from typing import Sequence

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment, AssignmentMaterial, Group, GroupMember
from app.models.class_ import Class, ClassMember
from app.models.enums import AssignmentType, GradeType, GradingType, MaterialType, MemberRole
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
        raise ClassError("FORBIDDEN", "Only teachers can manage assignments", 403)
    return cls


async def _ensure_member(db: AsyncSession, class_id: uuid.UUID, user: User) -> Class:
    cls = await classes_service.get_class_or_404(db, class_id)
    membership = await classes_service.get_membership(db, class_id, user.id)
    if membership is None and not user.is_admin:
        raise ClassError("FORBIDDEN", "You are not a member of this class", 403)
    return cls


def _serialize(
    assignment: Assignment,
    materials: Sequence[AssignmentMaterial],
    author: User,
) -> dict:
    return {
        "id": assignment.id,
        "class_id": assignment.class_id,
        "name": assignment.name,
        "description": assignment.description,
        "type": assignment.type,
        "grade_type": assignment.grade_type,
        "grading_type": assignment.grading_type,
        "group_count": assignment.group_count,
        "deadline": assignment.deadline,
        "author": {"id": author.id, "username": author.username},
        "created_at": assignment.created_at,
        "materials": [
            {
                "id": m.id,
                "material_type": m.material_type,
                "url": m.url,
                "file_name": m.file_name,
                "download_url": (
                    minio_storage.presigned_get_url(m.file_key, m.file_name)
                    if m.material_type == MaterialType.file and m.file_key
                    else None
                ),
            }
            for m in materials
        ],
    }


def _validate_create_params(
    type_: AssignmentType,
    grading_type: GradingType | None,
    group_count: int | None,
) -> None:
    if type_ == AssignmentType.group:
        if grading_type is None:
            raise ClassError("VALIDATION_ERROR", "grading_type is required for group assignments", 422)
        if group_count is None or group_count < 1:
            raise ClassError("VALIDATION_ERROR", "group_count must be positive for group assignments", 422)
    else:
        if grading_type is not None or group_count is not None:
            raise ClassError(
                "VALIDATION_ERROR",
                "grading_type and group_count must be null for individual assignments",
                422,
            )


async def create_assignment(
    db: AsyncSession,
    class_id: uuid.UUID,
    author: User,
    name: str,
    description: str | None,
    type_: AssignmentType,
    grade_type: GradeType,
    grading_type: GradingType | None,
    group_count: int | None,
    deadline: datetime | None,
    files: list[tuple[UploadFile, bytes]],
    links: list[str],
) -> dict:
    _validate_create_params(type_, grading_type, group_count)
    cls = await _ensure_teacher_in_class(db, class_id, author)

    uploaded_keys: list[str] = []
    file_records: list[tuple[str, str]] = []
    try:
        for upload, data in files:
            validate_upload(upload, len(data))
            key = minio_storage.build_key(cls.id, "assignments", upload.filename or "file")
            minio_storage.upload(key, data, upload.content_type or "application/octet-stream")
            uploaded_keys.append(key)
            file_records.append((key, upload.filename or "file"))

        assignment = Assignment(
            class_id=cls.id,
            author_id=author.id,
            name=name,
            description=description,
            type=type_,
            grade_type=grade_type,
            grading_type=grading_type,
            group_count=group_count,
            deadline=deadline,
        )
        db.add(assignment)
        await db.flush()

        for key, fname in file_records:
            db.add(AssignmentMaterial(
                assignment_id=assignment.id,
                material_type=MaterialType.file,
                file_key=key,
                file_name=fname,
            ))
        for link in links:
            db.add(AssignmentMaterial(
                assignment_id=assignment.id,
                material_type=MaterialType.link,
                url=link,
            ))
        await db.commit()
        await db.refresh(assignment)
    except Exception:
        await db.rollback()
        for key in uploaded_keys:
            minio_storage.delete(key)
        raise

    materials_result = await db.execute(
        select(AssignmentMaterial).where(AssignmentMaterial.assignment_id == assignment.id)
    )

    student_ids = await classes_service.get_member_ids(db, cls.id, roles=(MemberRole.student,))
    await notifications_service.notify(
        db,
        student_ids,
        "assignment_created",
        {
            "class_id": str(cls.id),
            "class_name": cls.name,
            "assignment_id": str(assignment.id),
            "name": assignment.name,
            "type": assignment.type.value,
            "deadline": assignment.deadline.isoformat() if assignment.deadline else None,
        },
    )
    await db.commit()

    return _serialize(assignment, list(materials_result.scalars().all()), author)


async def list_assignments(db: AsyncSession, class_id: uuid.UUID, current_user: User) -> list[dict]:
    await _ensure_member(db, class_id, current_user)

    result = await db.execute(
        select(Assignment)
        .where(Assignment.class_id == class_id)
        .order_by(Assignment.created_at.desc())
    )
    assignments = list(result.scalars().all())
    if not assignments:
        return []

    ids = [a.id for a in assignments]
    materials_result = await db.execute(
        select(AssignmentMaterial).where(AssignmentMaterial.assignment_id.in_(ids))
    )
    materials_by_assignment: dict[uuid.UUID, list[AssignmentMaterial]] = {}
    for m in materials_result.scalars().all():
        materials_by_assignment.setdefault(m.assignment_id, []).append(m)

    author_ids = list({a.author_id for a in assignments})
    authors_result = await db.execute(select(User).where(User.id.in_(author_ids)))
    authors = {u.id: u for u in authors_result.scalars().all()}

    return [
        _serialize(a, materials_by_assignment.get(a.id, []), authors[a.author_id])
        for a in assignments
    ]


async def get_assignment_detail(db: AsyncSession, assignment_id: uuid.UUID, current_user: User) -> dict:
    assignment = await _get_assignment_or_404(db, assignment_id)
    await _ensure_member(db, assignment.class_id, current_user)

    materials_result = await db.execute(
        select(AssignmentMaterial).where(AssignmentMaterial.assignment_id == assignment_id)
    )
    author_result = await db.execute(select(User).where(User.id == assignment.author_id))
    author = author_result.scalar_one()
    return _serialize(assignment, list(materials_result.scalars().all()), author)


async def _get_assignment_or_404(db: AsyncSession, assignment_id: uuid.UUID) -> Assignment:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise ClassError("ASSIGNMENT_NOT_FOUND", "Assignment not found", 404)
    return assignment


async def update_assignment(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    current_user: User,
    name: str | None,
    description: str | None,
    deadline: datetime | None,
) -> dict:
    assignment = await _get_assignment_or_404(db, assignment_id)
    membership = await classes_service.get_membership(db, assignment.class_id, current_user.id)
    if membership is None or not classes_service.is_teacher_role(membership.role):
        raise ClassError("FORBIDDEN", "Only teachers can update assignments", 403)

    if name is not None:
        assignment.name = name
    if description is not None:
        assignment.description = description
    if deadline is not None:
        assignment.deadline = deadline
    await db.commit()
    await db.refresh(assignment)
    return await get_assignment_detail(db, assignment.id, current_user)


async def delete_assignment(db: AsyncSession, assignment_id: uuid.UUID, current_user: User) -> None:
    assignment = await _get_assignment_or_404(db, assignment_id)

    is_author = assignment.author_id == current_user.id
    membership = await classes_service.get_membership(db, assignment.class_id, current_user.id)
    is_teacher = membership is not None and classes_service.is_teacher_role(membership.role)

    if not (is_author or is_teacher):
        raise ClassError("FORBIDDEN", "Only author or teachers can delete the assignment", 403)

    materials_result = await db.execute(
        select(AssignmentMaterial).where(AssignmentMaterial.assignment_id == assignment_id)
    )
    materials = list(materials_result.scalars().all())

    await db.delete(assignment)
    await db.commit()

    for m in materials:
        if m.file_key:
            minio_storage.delete(m.file_key)


async def _ensure_group_assignment_teacher(
    db: AsyncSession, assignment_id: uuid.UUID, current_user: User
) -> Assignment:
    assignment = await _get_assignment_or_404(db, assignment_id)
    if assignment.type != AssignmentType.group:
        raise ClassError("NOT_A_GROUP_ASSIGNMENT", "Groups are only for group assignments", 400)
    membership = await classes_service.get_membership(db, assignment.class_id, current_user.id)
    if membership is None or not classes_service.is_teacher_role(membership.role):
        raise ClassError("FORBIDDEN", "Only teachers can manage groups", 403)
    return assignment


async def _serialize_groups(db: AsyncSession, assignment_id: uuid.UUID) -> list[dict]:
    groups_result = await db.execute(
        select(Group).where(Group.assignment_id == assignment_id).order_by(Group.name.asc())
    )
    groups = list(groups_result.scalars().all())
    if not groups:
        return []

    group_ids = [g.id for g in groups]
    members_result = await db.execute(
        select(GroupMember, User)
        .join(User, User.id == GroupMember.user_id)
        .where(GroupMember.group_id.in_(group_ids))
    )
    members_by_group: dict[uuid.UUID, list[dict]] = {}
    for member, user in members_result.all():
        members_by_group.setdefault(member.group_id, []).append({
            "user_id": user.id,
            "username": user.username,
        })

    return [
        {
            "id": g.id,
            "name": g.name,
            "members": members_by_group.get(g.id, []),
        }
        for g in groups
    ]


async def _clear_groups(db: AsyncSession, assignment_id: uuid.UUID) -> None:
    existing = await db.execute(select(Group).where(Group.assignment_id == assignment_id))
    for g in existing.scalars().all():
        await db.delete(g)
    await db.flush()


async def create_groups_auto(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    current_user: User,
    group_count: int,
) -> list[dict]:
    assignment = await _ensure_group_assignment_teacher(db, assignment_id, current_user)

    students_result = await db.execute(
        select(User)
        .join(ClassMember, ClassMember.user_id == User.id)
        .where(
            ClassMember.class_id == assignment.class_id,
            ClassMember.role == MemberRole.student,
            User.deleted_at.is_(None),
        )
    )
    students = list(students_result.scalars().all())
    if not students:
        raise ClassError("NO_STUDENTS", "No students to distribute into groups", 400)
    if group_count > len(students):
        raise ClassError(
            "TOO_MANY_GROUPS",
            f"Cannot create {group_count} groups from {len(students)} students",
            400,
        )

    random.shuffle(students)
    buckets: list[list[User]] = [[] for _ in range(group_count)]
    for idx, student in enumerate(students):
        buckets[idx % group_count].append(student)

    await _clear_groups(db, assignment_id)

    for i, bucket in enumerate(buckets, start=1):
        group = Group(assignment_id=assignment_id, name=f"Group {i}")
        db.add(group)
        await db.flush()
        for student in bucket:
            db.add(GroupMember(group_id=group.id, user_id=student.id))
    await db.commit()

    return await _serialize_groups(db, assignment_id)


async def create_groups_manual(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    current_user: User,
    groups: list[list[uuid.UUID]],
) -> list[dict]:
    assignment = await _ensure_group_assignment_teacher(db, assignment_id, current_user)

    all_user_ids = [uid for group in groups for uid in group]
    if len(all_user_ids) != len(set(all_user_ids)):
        raise ClassError("DUPLICATE_USER", "A user cannot be in multiple groups", 400)

    members_result = await db.execute(
        select(ClassMember).where(
            ClassMember.class_id == assignment.class_id,
            ClassMember.user_id.in_(all_user_ids),
            ClassMember.role == MemberRole.student,
        )
    )
    valid_ids = {m.user_id for m in members_result.scalars().all()}
    if len(valid_ids) != len(set(all_user_ids)):
        raise ClassError(
            "INVALID_MEMBERS",
            "Some users are not students of this class",
            400,
        )

    await _clear_groups(db, assignment_id)

    for i, user_ids in enumerate(groups, start=1):
        group = Group(assignment_id=assignment_id, name=f"Group {i}")
        db.add(group)
        await db.flush()
        for uid in user_ids:
            db.add(GroupMember(group_id=group.id, user_id=uid))
    await db.commit()

    return await _serialize_groups(db, assignment_id)


async def list_groups(db: AsyncSession, assignment_id: uuid.UUID, current_user: User) -> list[dict]:
    assignment = await _get_assignment_or_404(db, assignment_id)
    await _ensure_member(db, assignment.class_id, current_user)
    return await _serialize_groups(db, assignment_id)
