"""End-to-end smoke test against a running LMS backend.

Walks the core happy path through real HTTP against the live API:

    health -> register teacher -> create class -> create assignment
           -> register student -> join class -> create+submit solution
           -> teacher grades -> grade shows up in the class grade matrix

Run it inside the backend container against the live app:

    docker compose exec backend python scripts/smoke_test.py

Or point it anywhere with BASE_URL:

    BASE_URL=http://localhost:8000 python backend/scripts/smoke_test.py

Exit code 0 = all steps passed, 1 = a step failed. Each run uses unique
emails (timestamp-based) so it is safe to re-run against a persistent DB.
"""
import os
import sys
import time

import httpx

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
STAMP = int(time.time())
TEACHER_EMAIL = f"smoke_teacher_{STAMP}@example.com"
STUDENT_EMAIL = f"smoke_student_{STAMP}@example.com"
PASSWORD = "password123"

_step = 0


def check(condition: bool, message: str) -> None:
    global _step
    _step += 1
    status = "OK  " if condition else "FAIL"
    print(f"  [{status}] {_step:>2}. {message}")
    if not condition:
        raise SystemExit(f"\nSmoke test FAILED at step {_step}: {message}")


def main() -> None:
    print(f"Smoke test against {BASE_URL}  (run id {STAMP})")

    # 1. health
    r = httpx.get(f"{BASE_URL}/health", timeout=10)
    check(r.status_code == 200, f"GET /health -> {r.status_code}")

    teacher = httpx.Client(base_url=BASE_URL, timeout=10)
    student = httpx.Client(base_url=BASE_URL, timeout=10)

    # 2. register teacher (cookies stored on the client)
    r = teacher.post("/api/auth/register", json={
        "email": TEACHER_EMAIL, "password": PASSWORD, "username": "Smoke Teacher"})
    check(r.status_code == 201, f"register teacher -> {r.status_code}")

    # 3. create a closed class (returns an invite code)
    r = teacher.post("/api/classes", json={"name": f"Smoke Class {STAMP}", "type": "closed"})
    check(r.status_code == 201, f"create class -> {r.status_code}")
    cls = r.json()
    class_id = cls["id"]
    invite_code = cls.get("invite_code")
    check(bool(invite_code), f"class has invite_code ({invite_code})")

    # 4. create an individual assignment (multipart form)
    r = teacher.post(f"/api/classes/{class_id}/assignments", data={
        "name": "Smoke Assignment", "type": "individual", "grade_type": "0-5"})
    check(r.status_code == 201, f"create assignment -> {r.status_code}")
    assignment_id = r.json()["id"]

    # 5. register student
    r = student.post("/api/auth/register", json={
        "email": STUDENT_EMAIL, "password": PASSWORD, "username": "Smoke Student"})
    check(r.status_code == 201, f"register student -> {r.status_code}")

    # 6. student joins the class by invite code
    r = student.post("/api/classes/join", json={"invite_code": invite_code})
    check(r.status_code == 200, f"student joins class -> {r.status_code}")

    # 7. student creates a solution draft
    r = student.post(f"/api/assignments/{assignment_id}/solutions", data={"text": "smoke solution"})
    check(r.status_code == 201, f"create solution -> {r.status_code}")
    solution_id = r.json()["id"]
    check(r.json()["status"] == "created", "solution status == created")

    # 8. student submits
    r = student.post(f"/api/solutions/{solution_id}/submit")
    check(r.status_code == 200 and r.json()["status"] == "submitted", "submit -> submitted")

    # 9. teacher grades
    r = teacher.post(f"/api/solutions/{solution_id}/grade", json={"grade": 5})
    check(r.status_code == 200 and r.json()["status"] == "graded", "grade -> graded")
    check(r.json()["grade"] == "5.00", "grade value == 5.00")

    # 10. grade appears in the class grade matrix
    r = teacher.get(f"/api/classes/{class_id}/grades")
    check(r.status_code == 200, f"grades summary -> {r.status_code}")
    summary = r.json()
    found = any(
        cell.get("grade") == "5.00"
        for stu in summary["students"]
        for cell in stu["grades"].values()
    )
    check(found, "graded value present in grade matrix")

    teacher.close()
    student.close()
    print("\nSmoke test PASSED — all steps OK.")


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as exc:
        print(f"\nHTTP error: {exc}", file=sys.stderr)
        raise SystemExit(1)
