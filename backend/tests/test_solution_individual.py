"""Solution lifecycle for an individual assignment: draft -> submit -> grade."""
import pytest

from app.models.enums import GradeType
from tests.factories import (
    add_member,
    auth_cookies,
    make_assignment,
    make_class,
    make_user,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _setup(db_session, *, grade_type=GradeType.grade_0_5):
    teacher = await make_user(db_session, username="Teacher")
    student = await make_user(db_session, username="Student")
    cls = await make_class(db_session, creator=teacher)
    await add_member(db_session, cls=cls, user=student)
    assignment = await make_assignment(
        db_session, cls=cls, author=teacher, grade_type=grade_type
    )
    return teacher, student, cls, assignment


async def test_individual_draft_submit_grade(client, db_session):
    teacher, student, cls, assignment = await _setup(db_session)

    # student creates a draft
    client.cookies.update(auth_cookies(student))
    create = await client.post(
        f"/api/assignments/{assignment.id}/solutions", data={"text": "my draft"}
    )
    assert create.status_code == 201, create.text
    sol = create.json()
    assert sol["status"] == "created"
    assert sol["text"] == "my draft"
    solution_id = sol["id"]

    # student submits
    submit = await client.post(f"/api/solutions/{solution_id}/submit")
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == "submitted"
    assert submit.json()["submitted_at"] is not None

    # teacher grades within range (0-5)
    client.cookies.update(auth_cookies(teacher))
    grade = await client.post(
        f"/api/solutions/{solution_id}/grade", json={"grade": 4}
    )
    assert grade.status_code == 200, grade.text
    body = grade.json()
    assert body["status"] == "graded"
    assert body["grade"] == "4.00"
    assert body["graded_at"] is not None


async def test_cannot_grade_before_submit(client, db_session):
    teacher, student, cls, assignment = await _setup(db_session)

    client.cookies.update(auth_cookies(student))
    create = await client.post(
        f"/api/assignments/{assignment.id}/solutions", data={"text": "draft"}
    )
    solution_id = create.json()["id"]

    # grading a 'created' (not submitted) solution is an invalid transition
    client.cookies.update(auth_cookies(teacher))
    resp = await client.post(f"/api/solutions/{solution_id}/grade", json={"grade": 3})
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "INVALID_TRANSITION"


async def test_grade_out_of_range_rejected(client, db_session):
    teacher, student, cls, assignment = await _setup(db_session, grade_type=GradeType.grade_0_5)

    client.cookies.update(auth_cookies(student))
    create = await client.post(
        f"/api/assignments/{assignment.id}/solutions", data={"text": "draft"}
    )
    solution_id = create.json()["id"]
    await client.post(f"/api/solutions/{solution_id}/submit")

    # 7 is out of the 0-5 range
    client.cookies.update(auth_cookies(teacher))
    resp = await client.post(f"/api/solutions/{solution_id}/grade", json={"grade": 7})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "GRADE_OUT_OF_RANGE"


async def test_student_cannot_grade(client, db_session):
    teacher, student, cls, assignment = await _setup(db_session)

    client.cookies.update(auth_cookies(student))
    create = await client.post(
        f"/api/assignments/{assignment.id}/solutions", data={"text": "draft"}
    )
    solution_id = create.json()["id"]
    await client.post(f"/api/solutions/{solution_id}/submit")

    # student tries to grade their own solution -> forbidden
    resp = await client.post(f"/api/solutions/{solution_id}/grade", json={"grade": 3})
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "FORBIDDEN"


async def test_duplicate_solution_rejected(client, db_session):
    teacher, student, cls, assignment = await _setup(db_session)

    client.cookies.update(auth_cookies(student))
    first = await client.post(
        f"/api/assignments/{assignment.id}/solutions", data={"text": "one"}
    )
    assert first.status_code == 201
    second = await client.post(
        f"/api/assignments/{assignment.id}/solutions", data={"text": "two"}
    )
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "SOLUTION_EXISTS"
