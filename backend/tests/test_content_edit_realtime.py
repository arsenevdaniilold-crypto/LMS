"""Editing announcements/assignments and the notifications that drive
real-time updates (created already covered elsewhere; here: updated/deleted)."""
import pytest
from sqlalchemy import select

from app.models.announcement import Announcement
from app.models.notification import Notification
from tests.factories import (
    add_member,
    auth_cookies,
    make_assignment,
    make_class,
    make_user,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _notif_types_for(db_session, user_id) -> set[str]:
    result = await db_session.execute(
        select(Notification.type).where(Notification.user_id == user_id)
    )
    return set(result.scalars().all())


# ----------------------------- Assignments -----------------------------

async def test_update_assignment_changes_fields_and_notifies_students(client, db_session):
    teacher = await make_user(db_session, username="Teacher")
    student = await make_user(db_session, username="Student")
    cls = await make_class(db_session, creator=teacher)
    await add_member(db_session, cls=cls, user=student)
    assignment = await make_assignment(db_session, cls=cls, author=teacher, name="Old name")

    client.cookies.update(auth_cookies(teacher))
    resp = await client.patch(
        f"/api/assignments/{assignment.id}",
        json={"name": "New name", "description": "Updated desc"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "New name"
    assert resp.json()["description"] == "Updated desc"

    # the student should have received an assignment_updated notification
    assert "assignment_updated" in await _notif_types_for(db_session, student.id)


async def test_delete_assignment_notifies_students(client, db_session):
    teacher = await make_user(db_session, username="Teacher")
    student = await make_user(db_session, username="Student")
    cls = await make_class(db_session, creator=teacher)
    await add_member(db_session, cls=cls, user=student)
    assignment = await make_assignment(db_session, cls=cls, author=teacher)

    client.cookies.update(auth_cookies(teacher))
    resp = await client.delete(f"/api/assignments/{assignment.id}")
    assert resp.status_code == 204, resp.text

    assert "assignment_deleted" in await _notif_types_for(db_session, student.id)


async def test_student_cannot_update_assignment(client, db_session):
    teacher = await make_user(db_session, username="Teacher")
    student = await make_user(db_session, username="Student")
    cls = await make_class(db_session, creator=teacher)
    await add_member(db_session, cls=cls, user=student)
    assignment = await make_assignment(db_session, cls=cls, author=teacher)

    client.cookies.update(auth_cookies(student))
    resp = await client.patch(f"/api/assignments/{assignment.id}", json={"name": "Hacked"})
    assert resp.status_code == 403, resp.text


# ----------------------------- Announcements -----------------------------

async def _make_announcement(db_session, cls, author, title="Old title", text="Old text"):
    ann = Announcement(class_id=cls.id, author_id=author.id, title=title, text=text)
    db_session.add(ann)
    await db_session.flush()
    return ann


async def test_update_announcement_changes_fields_and_notifies_members(client, db_session):
    teacher = await make_user(db_session, username="Teacher")
    student = await make_user(db_session, username="Student")
    cls = await make_class(db_session, creator=teacher)
    await add_member(db_session, cls=cls, user=student)
    ann = await _make_announcement(db_session, cls, teacher)

    client.cookies.update(auth_cookies(teacher))
    resp = await client.patch(
        f"/api/announcements/{ann.id}",
        json={"title": "New title", "text": "New text"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["title"] == "New title"
    assert resp.json()["text"] == "New text"

    assert "announcement_updated" in await _notif_types_for(db_session, student.id)


async def test_delete_announcement_notifies_members(client, db_session):
    teacher = await make_user(db_session, username="Teacher")
    student = await make_user(db_session, username="Student")
    cls = await make_class(db_session, creator=teacher)
    await add_member(db_session, cls=cls, user=student)
    ann = await _make_announcement(db_session, cls, teacher)

    client.cookies.update(auth_cookies(teacher))
    resp = await client.delete(f"/api/announcements/{ann.id}")
    assert resp.status_code == 204, resp.text

    assert "announcement_deleted" in await _notif_types_for(db_session, student.id)


async def test_update_announcement_validation(client, db_session):
    teacher = await make_user(db_session, username="Teacher")
    cls = await make_class(db_session, creator=teacher)
    ann = await _make_announcement(db_session, cls, teacher)

    client.cookies.update(auth_cookies(teacher))
    # empty title is rejected
    resp = await client.patch(f"/api/announcements/{ann.id}", json={"title": "   "})
    assert resp.status_code == 422, resp.text
