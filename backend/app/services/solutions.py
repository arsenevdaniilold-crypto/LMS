import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment, Group, GroupMember
from app.models.enums import AssignmentType, GradingType, MemberRole, SolutionStatus, GradeType
from app.models.solution import GradeRedistribution, Solution, SolutionFile
from app.models.user import User
from app.services import classes as classes_service
from app.services import notifications as notifications_service
from app.services.classes import ClassError
from app.services.minio_storage import minio_storage
from app.utils.files import validate_upload


GRADE_RANGES: dict[GradeType, tuple[Decimal, Decimal]] = {
    GradeType.grade_0_5: (Decimal("0"), Decimal("5")),
    GradeType.grade_0_100: (Decimal("0"), Decimal("100")),
    GradeType.grade_0_1: (Decimal("0"), Decimal("1")),
}

REDISTRIBUTION_TOLERANCE = Decimal("0.005")


def _validate_grade_in_range(grade: Decimal, grade_type: GradeType) -> None:
    lo, hi = GRADE_RANGES[grade_type]
    if grade < lo or grade > hi:
        raise ClassError(
            "GRADE_OUT_OF_RANGE",
            f"Grade {grade} must be in [{lo}, {hi}] for {grade_type.value}",
            422,
        )


async def _get_assignment_or_404(db: AsyncSession, assignment_id: uuid.UUID) -> Assignment:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise ClassError("ASSIGNMENT_NOT_FOUND", "Assignment not found", 404)
    return assignment


async def _get_solution_or_404(db: AsyncSession, solution_id: uuid.UUID) -> Solution:
    result = await db.execute(select(Solution).where(Solution.id == solution_id))
    solution = result.scalar_one_or_none()
    if solution is None:
        raise ClassError("SOLUTION_NOT_FOUND", "Solution not found", 404)
    return solution


async def _get_group_for_user(
    db: AsyncSession, assignment_id: uuid.UUID, user_id: uuid.UUID
) -> Group | None:
    result = await db.execute(
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(Group.assignment_id == assignment_id, GroupMember.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _get_group_members(db: AsyncSession, group_id: uuid.UUID) -> list[User]:
    result = await db.execute(
        select(User)
        .join(GroupMember, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
        .order_by(User.username.asc())
    )
    return list(result.scalars().all())


async def _serialize(db: AsyncSession, solution: Solution) -> dict:
    files_result = await db.execute(
        select(SolutionFile).where(SolutionFile.solution_id == solution.id)
    )
    files = files_result.scalars().all()

    creator_result = await db.execute(select(User).where(User.id == solution.creator_id))
    creator = creator_result.scalar_one()

    group_data = None
    if solution.group_id is not None:
        group_result = await db.execute(select(Group).where(Group.id == solution.group_id))
        group = group_result.scalar_one_or_none()
        if group is not None:
            members = await _get_group_members(db, group.id)
            group_data = {
                "id": group.id,
                "name": group.name,
                "members": [{"user_id": u.id, "username": u.username} for u in members],
            }

    redistribution = None
    if solution.status == SolutionStatus.graded or solution.status == SolutionStatus.pending_redistribution:
        rd_result = await db.execute(
            select(GradeRedistribution, User)
            .join(User, User.id == GradeRedistribution.user_id)
            .where(GradeRedistribution.solution_id == solution.id)
            .order_by(User.username.asc())
        )
        rd_rows = rd_result.all()
        if rd_rows:
            redistribution = [
                {"user_id": user.id, "username": user.username, "grade": gr.grade}
                for gr, user in rd_rows
            ]

    return {
        "id": solution.id,
        "assignment_id": solution.assignment_id,
        "creator_id": solution.creator_id,
        "creator_username": creator.username,
        "group": group_data,
        "text": solution.text,
        "status": solution.status,
        "grade": solution.grade,
        "submitted_at": solution.submitted_at,
        "graded_at": solution.graded_at,
        "created_at": solution.created_at,
        "updated_at": solution.updated_at,
        "files": [
            {
                "id": f.id,
                "file_name": f.file_name,
                "file_size": f.file_size,
                "download_url": minio_storage.presigned_get_url(f.file_key, f.file_name),
            }
            for f in files
        ],
        "redistribution": redistribution,
    }


async def _ensure_class_member(db: AsyncSession, assignment: Assignment, user: User):
    membership = await classes_service.get_membership(db, assignment.class_id, user.id)
    if membership is None and not user.is_admin:
        raise ClassError("FORBIDDEN", "You are not a member of this class", 403)
    return membership


async def _resolve_create_context(
    db: AsyncSession, assignment: Assignment, current_user: User
) -> Group | None:
    """For create_solution: returns group user belongs to (or None for individual).
    Raises if group-assignment and user not in any group."""
    if assignment.type == AssignmentType.individual:
        return None
    group = await _get_group_for_user(db, assignment.id, current_user.id)
    if group is None:
        raise ClassError("NOT_IN_GROUP", "You are not assigned to any group for this assignment", 403)
    return group


async def _replace_solution_files(
    db: AsyncSession,
    solution: Solution,
    new_files: list[tuple[UploadFile, bytes]],
    class_id: uuid.UUID,
) -> list[str]:
    """Delete existing files, upload new ones; return list of new Minio keys for rollback."""
    existing_result = await db.execute(
        select(SolutionFile).where(SolutionFile.solution_id == solution.id)
    )
    existing = list(existing_result.scalars().all())
    for f in existing:
        await db.delete(f)
    await db.flush()

    uploaded_keys: list[str] = []
    for upload, data in new_files:
        validate_upload(upload, len(data), allow_xlsx=True)
        key = minio_storage.build_key(class_id, "solutions", upload.filename or "file")
        minio_storage.upload(key, data, upload.content_type or "application/octet-stream")
        uploaded_keys.append(key)
        db.add(SolutionFile(
            solution_id=solution.id,
            file_key=key,
            file_name=upload.filename or "file",
            file_size=len(data),
        ))

    for f in existing:
        minio_storage.delete(f.file_key)
    return uploaded_keys


async def create_solution(
    db: AsyncSession,
    assignment_id: uuid.UUID,
    current_user: User,
    text: str | None,
    files: list[tuple[UploadFile, bytes]],
) -> dict:
    assignment = await _get_assignment_or_404(db, assignment_id)
    await _ensure_class_member(db, assignment, current_user)

    group = await _resolve_create_context(db, assignment, current_user)

    existing_stmt = select(Solution).where(Solution.assignment_id == assignment_id)
    if group is not None:
        existing_stmt = existing_stmt.where(Solution.group_id == group.id)
    else:
        existing_stmt = existing_stmt.where(Solution.creator_id == current_user.id, Solution.group_id.is_(None))
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing is not None:
        raise ClassError("SOLUTION_EXISTS", "Solution already exists for this assignment", 409)

    solution = Solution(
        assignment_id=assignment_id,
        group_id=group.id if group else None,
        creator_id=current_user.id,
        text=text,
        status=SolutionStatus.created,
    )
    db.add(solution)
    await db.flush()

    uploaded_keys: list[str] = []
    try:
        for upload, data in files:
            validate_upload(upload, len(data), allow_xlsx=True)
            key = minio_storage.build_key(assignment.class_id, "solutions", upload.filename or "file")
            minio_storage.upload(key, data, upload.content_type or "application/octet-stream")
            uploaded_keys.append(key)
            db.add(SolutionFile(
                solution_id=solution.id,
                file_key=key,
                file_name=upload.filename or "file",
                file_size=len(data),
            ))
        await db.commit()
        await db.refresh(solution)
    except Exception:
        await db.rollback()
        for key in uploaded_keys:
            minio_storage.delete(key)
        raise

    return await _serialize(db, solution)


async def update_solution(
    db: AsyncSession,
    solution_id: uuid.UUID,
    current_user: User,
    text: str | None,
    files: list[tuple[UploadFile, bytes]],
) -> dict:
    solution = await _get_solution_or_404(db, solution_id)
    assignment = await _get_assignment_or_404(db, solution.assignment_id)
    await _ensure_class_member(db, assignment, current_user)

    if assignment.type == AssignmentType.individual:
        if solution.creator_id != current_user.id:
            raise ClassError("FORBIDDEN", "Only solution owner can edit", 403)
    else:
        group = await _get_group_for_user(db, assignment.id, current_user.id)
        if group is None or group.id != solution.group_id:
            raise ClassError("FORBIDDEN", "Only group members can edit", 403)

    if solution.status not in (SolutionStatus.created, SolutionStatus.returned):
        raise ClassError(
            "CANNOT_EDIT",
            f"Cannot edit solution in status '{solution.status.value}'",
            403,
        )

    if text is not None:
        solution.text = text

    uploaded_keys: list[str] = []
    try:
        uploaded_keys = await _replace_solution_files(db, solution, files, assignment.class_id)
        await db.commit()
        await db.refresh(solution)
    except Exception:
        await db.rollback()
        for key in uploaded_keys:
            minio_storage.delete(key)
        raise

    return await _serialize(db, solution)


async def list_solutions(
    db: AsyncSession, assignment_id: uuid.UUID, current_user: User
) -> list[dict]:
    assignment = await _get_assignment_or_404(db, assignment_id)
    membership = await _ensure_class_member(db, assignment, current_user)

    is_teacher = (
        membership is not None and classes_service.is_teacher_role(membership.role)
    ) or current_user.is_admin

    stmt = select(Solution).where(Solution.assignment_id == assignment_id)
    if not is_teacher:
        if assignment.type == AssignmentType.individual:
            stmt = stmt.where(Solution.creator_id == current_user.id)
        else:
            group = await _get_group_for_user(db, assignment_id, current_user.id)
            if group is None:
                return []
            stmt = stmt.where(Solution.group_id == group.id)

    stmt = stmt.order_by(Solution.created_at.desc())
    solutions = list((await db.execute(stmt)).scalars().all())
    return [await _serialize(db, s) for s in solutions]


async def get_solution_detail(
    db: AsyncSession, solution_id: uuid.UUID, current_user: User
) -> dict:
    solution = await _get_solution_or_404(db, solution_id)
    assignment = await _get_assignment_or_404(db, solution.assignment_id)
    membership = await _ensure_class_member(db, assignment, current_user)

    is_teacher = (
        membership is not None and classes_service.is_teacher_role(membership.role)
    ) or current_user.is_admin

    if not is_teacher:
        if assignment.type == AssignmentType.individual:
            if solution.creator_id != current_user.id:
                raise ClassError("FORBIDDEN", "You cannot view this solution", 403)
        else:
            group = await _get_group_for_user(db, assignment.id, current_user.id)
            if group is None or group.id != solution.group_id:
                raise ClassError("FORBIDDEN", "You cannot view this solution", 403)

    return await _serialize(db, solution)


async def submit_solution(
    db: AsyncSession, solution_id: uuid.UUID, current_user: User
) -> dict:
    solution = await _get_solution_or_404(db, solution_id)
    assignment = await _get_assignment_or_404(db, solution.assignment_id)
    await _ensure_class_member(db, assignment, current_user)

    if assignment.type == AssignmentType.individual:
        if solution.creator_id != current_user.id:
            raise ClassError("FORBIDDEN", "Only solution owner can submit", 403)
    else:
        group = await _get_group_for_user(db, assignment.id, current_user.id)
        if group is None or group.id != solution.group_id:
            raise ClassError("FORBIDDEN", "Only group members can submit", 403)

    if solution.status not in (SolutionStatus.created, SolutionStatus.returned):
        raise ClassError(
            "INVALID_TRANSITION",
            f"Cannot submit from status '{solution.status.value}'",
            409,
        )

    if assignment.deadline is not None and datetime.now(timezone.utc) > assignment.deadline:
        raise ClassError("DEADLINE_PASSED", "Assignment deadline has passed", 403)

    solution.status = SolutionStatus.submitted
    solution.submitted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(solution)
    return await _serialize(db, solution)


async def _solution_recipients(db: AsyncSession, solution: Solution) -> list[uuid.UUID]:
    if solution.group_id is not None:
        members = await _get_group_members(db, solution.group_id)
        return [m.id for m in members]
    return [solution.creator_id]


async def _ensure_teacher(db: AsyncSession, assignment: Assignment, current_user: User) -> None:
    membership = await classes_service.get_membership(db, assignment.class_id, current_user.id)
    if (membership is None or not classes_service.is_teacher_role(membership.role)) and not current_user.is_admin:
        raise ClassError("FORBIDDEN", "Only teachers can perform this action", 403)


async def return_solution(
    db: AsyncSession, solution_id: uuid.UUID, current_user: User
) -> dict:
    solution = await _get_solution_or_404(db, solution_id)
    assignment = await _get_assignment_or_404(db, solution.assignment_id)
    await _ensure_teacher(db, assignment, current_user)

    if solution.status != SolutionStatus.submitted:
        raise ClassError(
            "INVALID_TRANSITION",
            f"Cannot return from status '{solution.status.value}'",
            409,
        )
    solution.status = SolutionStatus.returned
    await db.flush()
    await notifications_service.notify(
        db,
        await _solution_recipients(db, solution),
        "solution_returned",
        {
            "solution_id": str(solution.id),
            "assignment_id": str(assignment.id),
            "assignment_name": assignment.name,
            "class_id": str(assignment.class_id),
        },
    )
    await db.commit()
    await db.refresh(solution)
    return await _serialize(db, solution)


async def grade_solution(
    db: AsyncSession, solution_id: uuid.UUID, current_user: User, grade: Decimal
) -> dict:
    solution = await _get_solution_or_404(db, solution_id)
    assignment = await _get_assignment_or_404(db, solution.assignment_id)
    await _ensure_teacher(db, assignment, current_user)

    if solution.status != SolutionStatus.submitted:
        raise ClassError(
            "INVALID_TRANSITION",
            f"Cannot grade from status '{solution.status.value}'",
            409,
        )
    _validate_grade_in_range(grade, assignment.grade_type)

    solution.grade = grade
    solution.graded_at = datetime.now(timezone.utc)
    if (
        assignment.type == AssignmentType.group
        and assignment.grading_type == GradingType.individual
    ):
        solution.status = SolutionStatus.pending_redistribution
        notif_type = "solution_pending_redistribution"
    else:
        solution.status = SolutionStatus.graded
        notif_type = "solution_graded"

    await db.flush()
    await notifications_service.notify(
        db,
        await _solution_recipients(db, solution),
        notif_type,
        {
            "solution_id": str(solution.id),
            "assignment_id": str(assignment.id),
            "assignment_name": assignment.name,
            "class_id": str(assignment.class_id),
            "grade": str(solution.grade) if solution.grade is not None else None,
        },
    )
    await db.commit()
    await db.refresh(solution)
    return await _serialize(db, solution)


async def redistribute_solution(
    db: AsyncSession,
    solution_id: uuid.UUID,
    current_user: User,
    entries: list[tuple[uuid.UUID, Decimal]],
) -> dict:
    solution = await _get_solution_or_404(db, solution_id)
    assignment = await _get_assignment_or_404(db, solution.assignment_id)
    await _ensure_class_member(db, assignment, current_user)

    if assignment.type != AssignmentType.group or assignment.grading_type != GradingType.individual:
        raise ClassError(
            "NOT_INDIVIDUAL_GROUP",
            "Redistribution is only for group assignments with individual grading",
            400,
        )

    if solution.status != SolutionStatus.pending_redistribution:
        raise ClassError(
            "INVALID_TRANSITION",
            f"Cannot redistribute from status '{solution.status.value}'",
            409,
        )

    if solution.group_id is None:
        raise ClassError("INTERNAL", "Group solution missing group_id", 500)
    members = await _get_group_members(db, solution.group_id)
    member_ids = {m.id for m in members}

    if current_user.id not in member_ids and not current_user.is_admin:
        raise ClassError("FORBIDDEN", "Only group members can redistribute", 403)

    entry_ids = {uid for uid, _ in entries}
    if entry_ids != member_ids:
        raise ClassError(
            "MEMBER_MISMATCH",
            "Redistribution must cover exactly all group members",
            422,
        )

    for _, g in entries:
        _validate_grade_in_range(g, assignment.grade_type)

    total = sum((g for _, g in entries), Decimal("0"))
    mean = total / Decimal(len(entries))
    if abs(mean - (solution.grade or Decimal("0"))) > REDISTRIBUTION_TOLERANCE:
        raise ClassError(
            "MEAN_MISMATCH",
            f"Mean {mean} must equal solution.grade {solution.grade} (tolerance {REDISTRIBUTION_TOLERANCE})",
            422,
        )

    existing_result = await db.execute(
        select(GradeRedistribution).where(GradeRedistribution.solution_id == solution.id)
    )
    for r in existing_result.scalars().all():
        await db.delete(r)
    await db.flush()

    for uid, g in entries:
        db.add(GradeRedistribution(solution_id=solution.id, user_id=uid, grade=g))

    solution.status = SolutionStatus.graded
    await db.flush()
    await notifications_service.notify(
        db,
        [m.id for m in members],
        "solution_graded",
        {
            "solution_id": str(solution.id),
            "assignment_id": str(assignment.id),
            "assignment_name": assignment.name,
            "class_id": str(assignment.class_id),
            "redistributed": True,
        },
    )
    await db.commit()
    await db.refresh(solution)
    return await _serialize(db, solution)
