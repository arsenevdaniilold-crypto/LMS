"""Group assignment + individual grading: grade -> redistribute, with the
mean-equality (±0.005), full-member-coverage, and grade-range rules enforced."""
import pytest

from app.models.enums import AssignmentType, GradeType, GradingType
from tests.factories import (
    add_member,
    auth_cookies,
    make_assignment,
    make_class,
    make_group,
    make_user,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _setup_group_pending(client, db_session, *, grade, grade_type):
    """Build a 2-member group solution, submit and grade it so it lands in
    `pending_redistribution`. Returns (teacher, s1, s2, solution_id)."""
    teacher = await make_user(db_session, username="Teacher")
    s1 = await make_user(db_session, username="Alpha")
    s2 = await make_user(db_session, username="Beta")
    cls = await make_class(db_session, creator=teacher)
    await add_member(db_session, cls=cls, user=s1)
    await add_member(db_session, cls=cls, user=s2)
    assignment = await make_assignment(
        db_session,
        cls=cls,
        author=teacher,
        type_=AssignmentType.group,
        grading_type=GradingType.individual,
        group_count=1,
        grade_type=grade_type,
    )
    await make_group(db_session, assignment=assignment, members=[s1, s2])

    # s1 creates+submits the group solution
    client.cookies.update(auth_cookies(s1))
    create = await client.post(
        f"/api/assignments/{assignment.id}/solutions", data={"text": "group work"}
    )
    assert create.status_code == 201, create.text
    solution_id = create.json()["id"]
    submit = await client.post(f"/api/solutions/{solution_id}/submit")
    assert submit.status_code == 200, submit.text

    # teacher grades the group -> pending_redistribution
    client.cookies.update(auth_cookies(teacher))
    graded = await client.post(
        f"/api/solutions/{solution_id}/grade", json={"grade": grade}
    )
    assert graded.status_code == 200, graded.text
    assert graded.json()["status"] == "pending_redistribution"

    return teacher, s1, s2, solution_id


async def test_valid_redistribution_succeeds(client, db_session):
    teacher, s1, s2, solution_id = await _setup_group_pending(
        client, db_session, grade=4, grade_type=GradeType.grade_0_5
    )

    # mean of [3, 5] == 4 == group grade
    client.cookies.update(auth_cookies(s1))
    resp = await client.post(
        f"/api/solutions/{solution_id}/redistribute",
        json={"grades": [
            {"user_id": str(s1.id), "grade": 3},
            {"user_id": str(s2.id), "grade": 5},
        ]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "graded"
    by_user = {r["user_id"]: r["grade"] for r in body["redistribution"]}
    assert by_user[str(s1.id)] == "3.00"
    assert by_user[str(s2.id)] == "5.00"


async def test_mean_within_tolerance_succeeds(client, db_session):
    # 0-100 scale, grade 50; [49.99, 50.01] -> mean exactly 50.00 (within ±0.005)
    teacher, s1, s2, solution_id = await _setup_group_pending(
        client, db_session, grade=50, grade_type=GradeType.grade_0_100
    )
    client.cookies.update(auth_cookies(s1))
    resp = await client.post(
        f"/api/solutions/{solution_id}/redistribute",
        json={"grades": [
            {"user_id": str(s1.id), "grade": 49.99},
            {"user_id": str(s2.id), "grade": 50.01},
        ]},
    )
    assert resp.status_code == 200, resp.text


async def test_mean_mismatch_rejected(client, db_session):
    teacher, s1, s2, solution_id = await _setup_group_pending(
        client, db_session, grade=4, grade_type=GradeType.grade_0_5
    )
    # mean of [2, 5] == 3.5 != 4
    client.cookies.update(auth_cookies(s1))
    resp = await client.post(
        f"/api/solutions/{solution_id}/redistribute",
        json={"grades": [
            {"user_id": str(s1.id), "grade": 2},
            {"user_id": str(s2.id), "grade": 5},
        ]},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "MEAN_MISMATCH"


async def test_member_mismatch_rejected(client, db_session):
    teacher, s1, s2, solution_id = await _setup_group_pending(
        client, db_session, grade=4, grade_type=GradeType.grade_0_5
    )
    # only covers one of the two members
    client.cookies.update(auth_cookies(s1))
    resp = await client.post(
        f"/api/solutions/{solution_id}/redistribute",
        json={"grades": [{"user_id": str(s1.id), "grade": 4}]},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "MEMBER_MISMATCH"


async def test_redistribution_grade_out_of_range_rejected(client, db_session):
    teacher, s1, s2, solution_id = await _setup_group_pending(
        client, db_session, grade=4, grade_type=GradeType.grade_0_5
    )
    # 6 exceeds the 0-5 max even though the mean of [2, 6] == 4
    client.cookies.update(auth_cookies(s1))
    resp = await client.post(
        f"/api/solutions/{solution_id}/redistribute",
        json={"grades": [
            {"user_id": str(s1.id), "grade": 2},
            {"user_id": str(s2.id), "grade": 6},
        ]},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "GRADE_OUT_OF_RANGE"
