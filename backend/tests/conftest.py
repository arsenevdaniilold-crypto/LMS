"""Test fixtures for the LMS backend.

These tests are designed to run **inside the backend container**, where all
dependencies and a reachable Postgres (`postgres:5432`) are available:

    docker compose exec backend python -m pytest

A dedicated database `lms_test` is created on the same Postgres instance, the
schema is built from SQLAlchemy metadata (with the Postgres ENUM types created
explicitly, since the models declare them with ``create_type=False``), and each
test runs inside a transaction that is rolled back afterwards, so tests never
pollute each other or the dev database.
"""
from typing import AsyncIterator
from urllib.parse import urlsplit, urlunsplit

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)

from app.config import settings
from app.database import get_db
from app.limiter import limiter
from app.main import app as fastapi_app
from app.models.base import Base
import app.models as _models  # noqa: F401 — register all models on Base.metadata


# --- ENUM types (mirror alembic/versions/0001_initial.py) -------------------
# Base.metadata.create_all won't emit these because the models use
# create_type=False, so we create them by hand before create_all.
_ENUM_DDL = [
    "CREATE TYPE class_type AS ENUM ('open', 'closed')",
    "CREATE TYPE member_role AS ENUM ('teacher_creator', 'teacher', 'student')",
    "CREATE TYPE assignment_type AS ENUM ('individual', 'group')",
    "CREATE TYPE grade_type AS ENUM ('0-5', '0-100', '0-1')",
    "CREATE TYPE grading_type AS ENUM ('uniform', 'individual')",
    "CREATE TYPE material_type AS ENUM ('link', 'file')",
    "CREATE TYPE solution_status AS ENUM "
    "('created', 'submitted', 'returned', 'graded', 'pending_redistribution')",
]

TEST_DB_NAME = "lms_test"


def _swap_database(url: str, db_name: str) -> str:
    parts = urlsplit(url)
    new_path = "/" + db_name
    return urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))


TEST_DATABASE_URL = _swap_database(settings.database_url, TEST_DB_NAME)
ADMIN_DATABASE_URL = _swap_database(settings.database_url, "postgres")


@pytest_asyncio.fixture(scope="session")
async def _setup_database() -> AsyncIterator[None]:
    """Drop & recreate the lms_test database and build its schema once per session.

    Each engine here is disposed before the fixture returns, so no asyncpg
    connection outlives the loop it was created on (per-test loops are used for
    the actual queries via the function-scoped ``engine`` fixture).
    """
    admin_engine = create_async_engine(
        ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with admin_engine.connect() as conn:
        await conn.exec_driver_sql(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            f"WHERE datname = '{TEST_DB_NAME}' AND pid <> pg_backend_pid()"
        )
        await conn.exec_driver_sql(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
        await conn.exec_driver_sql(f'CREATE DATABASE "{TEST_DB_NAME}"')
    await admin_engine.dispose()

    schema_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with schema_engine.begin() as conn:
        for ddl in _ENUM_DDL:
            await conn.exec_driver_sql(ddl)
        await conn.run_sync(Base.metadata.create_all)
    await schema_engine.dispose()
    yield


@pytest_asyncio.fixture()
async def engine(_setup_database):
    """Per-test engine (NullPool) so connections live on the test's own loop."""
    eng = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture()
async def db_session(engine) -> AsyncIterator[AsyncSession]:
    """Per-test session wrapped in a transaction that is rolled back.

    Uses an outer transaction + SAVEPOINT so that `commit()` calls inside the
    services (auth/solutions/...) don't actually persist — when the inner
    SAVEPOINT is released, we immediately open a new one. Everything is undone
    on teardown by rolling back the outer transaction.
    """
    connection = await engine.connect()
    trans = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    await connection.begin_nested()

    from sqlalchemy import event

    @event.listens_for(session.sync_session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            connection.sync_connection.begin_nested()

    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest_asyncio.fixture()
async def client(db_session) -> AsyncIterator[AsyncClient]:
    """HTTP client talking to the ASGI app, with get_db overridden to the test
    session and the rate limiter disabled."""
    async def _override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    limiter.enabled = False
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()
    limiter.enabled = True
