"""Direct-to-DB seed helpers for tests.

These build prerequisite rows (users, classes, memberships, assignments,
groups) straight through the test session, so tests can focus on exercising
the behaviour under test (e.g. the solution lifecycle) over HTTP without
juggling multipart create endpoints or Minio.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment, Group, GroupMember
from app.models.class_ import Class, ClassMember
from app.models.enums import (
    AssignmentType,
    ClassType,
    GradeType,
    GradingType,
    MemberRole,
)
from app.models.user import User
from app.utils.security import create_access_token, hash_password


async def make_user(
    db: AsyncSession,
    *,
    email: str | None = None,
    username: str = "User",
    password: str = "password123",
    is_admin: bool = False,
) -> User:
    user = User(
        email=email or f"{uuid.uuid4().hex[:10]}@example.com",
        password_hash=hash_password(password),
        username=username,
        is_admin=is_admin,
    )
    db.add(user)
    await db.flush()
    return user


def auth_cookies(user: User) -> dict[str, str]:
    """Cookies that authenticate an HTTP client as ``user``."""
    return {"access_token": create_access_token(str(user.id))}


async def make_class(
    db: AsyncSession,
    *,
    creator: User,
    name: str = "Test Class",
    type_: ClassType = ClassType.closed,
) -> Class:
    cls = Class(name=name, type=type_, creator_id=creator.id)
    db.add(cls)
    await db.flush()
    db.add(ClassMember(class_id=cls.id, user_id=creator.id, role=MemberRole.teacher_creator))
    await db.flush()
    return cls


async def add_member(
    db: AsyncSession,
    *,
    cls: Class,
    user: User,
    role: MemberRole = MemberRole.student,
) -> ClassMember:
    member = ClassMember(class_id=cls.id, user_id=user.id, role=role)
    db.add(member)
    await db.flush()
    return member


async def make_assignment(
    db: AsyncSession,
    *,
    cls: Class,
    author: User,
    name: str = "Assignment",
    type_: AssignmentType = AssignmentType.individual,
    grade_type: GradeType = GradeType.grade_0_5,
    grading_type: GradingType | None = None,
    group_count: int | None = None,
    deadline: datetime | None = None,
) -> Assignment:
    assignment = Assignment(
        class_id=cls.id,
        author_id=author.id,
        name=name,
        type=type_,
        grade_type=grade_type,
        grading_type=grading_type,
        group_count=group_count,
        deadline=deadline,
    )
    db.add(assignment)
    await db.flush()
    return assignment


async def make_group(
    db: AsyncSession,
    *,
    assignment: Assignment,
    members: list[User],
    name: str = "Group 1",
) -> Group:
    group = Group(assignment_id=assignment.id, name=name)
    db.add(group)
    await db.flush()
    for u in members:
        db.add(GroupMember(group_id=group.id, user_id=u.id))
    await db.flush()
    return group
