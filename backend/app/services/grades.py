import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment, Group, GroupMember
from app.models.class_ import ClassMember
from app.models.enums import AssignmentType, GradingType, MemberRole
from app.models.solution import GradeRedistribution, Solution
from app.models.user import User
from app.services import classes as classes_service
from app.services.classes import ClassError


GRADE_SCALE_MAX: dict[str, Decimal] = {
    "0-5": Decimal("5"),
    "0-100": Decimal("100"),
    "0-1": Decimal("1"),
}


def _normalize_average(values: list[tuple[Decimal, str]]) -> Decimal | None:
    """Compute an average grade normalized to the 0..100 scale.

    Each ``(grade, scale)`` is rescaled to 0..100 first, then we take the
    arithmetic mean (the user explicitly asked for the simple mean across
    assignments — even when the underlying grade scales differ)."""
    if not values:
        return None
    total = Decimal("0")
    for grade, scale in values:
        max_v = GRADE_SCALE_MAX.get(scale, Decimal("100"))
        if max_v == 0:
            continue
        total += (grade / max_v) * Decimal("100")
    avg = total / Decimal(len(values))
    return avg.quantize(Decimal("0.01"))


async def get_class_grades(
    db: AsyncSession, class_id: uuid.UUID, current_user: User
) -> dict:
    await classes_service.get_class_or_404(db, class_id)
    membership = await classes_service.get_membership(db, class_id, current_user.id)
    if membership is None and not current_user.is_admin:
        raise ClassError("FORBIDDEN", "You are not a member of this class", 403)

    # If the viewer is a *student* in this class, hide other students even if
    # they happen to be a platform admin. Admin power-view is only for users
    # who aren't enrolled as students in this specific class.
    is_student_member = (
        membership is not None
        and membership.role == MemberRole.student
    )
    is_teacher_view = not is_student_member and (
        (membership is not None and classes_service.is_teacher_role(membership.role))
        or current_user.is_admin
    )

    students_stmt = (
        select(User)
        .join(ClassMember, ClassMember.user_id == User.id)
        .where(
            ClassMember.class_id == class_id,
            ClassMember.role == MemberRole.student,
            User.deleted_at.is_(None),
        )
        .order_by(User.username.asc())
    )
    if not is_teacher_view:
        students_stmt = students_stmt.where(User.id == current_user.id)
    students_result = await db.execute(students_stmt)
    students = list(students_result.scalars().all())

    assignments_result = await db.execute(
        select(Assignment)
        .where(Assignment.class_id == class_id)
        .order_by(Assignment.created_at.asc())
    )
    assignments = list(assignments_result.scalars().all())

    solutions_result = await db.execute(
        select(Solution).where(Solution.assignment_id.in_([a.id for a in assignments]) if assignments else False)
    )
    solutions = list(solutions_result.scalars().all())

    group_member_result = await db.execute(
        select(GroupMember, Group)
        .join(Group, Group.id == GroupMember.group_id)
        .where(Group.assignment_id.in_([a.id for a in assignments]) if assignments else False)
    )
    user_to_group: dict[tuple[uuid.UUID, uuid.UUID], uuid.UUID] = {}
    for gm, group in group_member_result.all():
        user_to_group[(group.assignment_id, gm.user_id)] = group.id

    redistributions_result = await db.execute(
        select(GradeRedistribution).where(
            GradeRedistribution.solution_id.in_([s.id for s in solutions]) if solutions else False
        )
    )
    redistributions: dict[tuple[uuid.UUID, uuid.UUID], Decimal] = {}
    for r in redistributions_result.scalars().all():
        redistributions[(r.solution_id, r.user_id)] = r.grade

    solutions_index: dict[uuid.UUID, list[Solution]] = {}
    for s in solutions:
        solutions_index.setdefault(s.assignment_id, []).append(s)

    students_payload = []
    for student in students:
        cells: dict[uuid.UUID, dict] = {}
        grade_pairs: list[tuple[Decimal, str]] = []
        for assignment in assignments:
            assignment_solutions = solutions_index.get(assignment.id, [])
            cell: dict = {"solution_id": None, "status": None, "grade": None}

            if assignment.type == AssignmentType.individual:
                relevant = next((s for s in assignment_solutions if s.creator_id == student.id), None)
            else:
                group_id = user_to_group.get((assignment.id, student.id))
                relevant = next((s for s in assignment_solutions if s.group_id == group_id), None) if group_id else None

            if relevant is not None:
                cell["solution_id"] = relevant.id
                cell["status"] = relevant.status
                if (
                    assignment.type == AssignmentType.group
                    and assignment.grading_type == GradingType.individual
                ):
                    cell["grade"] = redistributions.get((relevant.id, student.id))
                else:
                    cell["grade"] = relevant.grade
            cells[assignment.id] = cell
            if cell["grade"] is not None:
                grade_pairs.append((cell["grade"], assignment.grade_type.value))

        students_payload.append({
            "user_id": student.id,
            "username": student.username,
            "grades": cells,
            "average": _normalize_average(grade_pairs),
        })

    class_avg_values = [
        (cell["grade"], next(a for a in assignments if a.id == aid).grade_type.value)
        for student in students_payload
        for aid, cell in student["grades"].items()
        if cell["grade"] is not None
    ]
    class_average = _normalize_average(class_avg_values) if is_teacher_view else None

    return {
        "viewer_role": (
            "teacher" if is_teacher_view else "student"
        ),
        "assignments": [
            {
                "id": a.id,
                "name": a.name,
                "grade_type": a.grade_type.value,
                "type": a.type.value,
            }
            for a in assignments
        ],
        "students": students_payload,
        "class_average": class_average,
    }
