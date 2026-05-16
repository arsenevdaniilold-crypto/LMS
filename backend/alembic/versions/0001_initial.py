"""initial

Revision ID: 0001
Revises:
Create Date: 2026-05-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enum types ---
    op.execute("CREATE TYPE class_type AS ENUM ('open', 'closed')")
    op.execute("CREATE TYPE member_role AS ENUM ('teacher_creator', 'teacher', 'student')")
    op.execute("CREATE TYPE assignment_type AS ENUM ('individual', 'group')")
    op.execute("CREATE TYPE grade_type AS ENUM ('0-5', '0-100', '0-1')")
    op.execute("CREATE TYPE grading_type AS ENUM ('uniform', 'individual')")
    op.execute("CREATE TYPE material_type AS ENUM ('link', 'file')")
    op.execute("CREATE TYPE solution_status AS ENUM ('created', 'submitted', 'returned', 'graded', 'pending_redistribution')")

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    # --- classes ---
    op.create_table(
        "classes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", postgresql.ENUM("open", "closed", name="class_type", create_type=False), nullable=False),
        sa.Column("invite_code", sa.String(8), nullable=True),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_classes_type", "classes", ["type"])
    op.create_index("ix_classes_deleted_at", "classes", ["deleted_at"])
    op.create_index("uq_classes_invite_code", "classes", ["invite_code"], unique=True)

    # --- class_members ---
    op.create_table(
        "class_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", postgresql.ENUM("teacher_creator", "teacher", "student", name="member_role", create_type=False), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("class_id", "user_id", name="uq_class_members_class_user"),
    )
    op.create_index("ix_class_members_class_id", "class_members", ["class_id"])
    op.create_index("ix_class_members_user_id", "class_members", ["user_id"])

    # --- announcements ---
    op.create_table(
        "announcements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_announcements_class_id", "announcements", ["class_id"])

    # --- announcement_files ---
    op.create_table(
        "announcement_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("announcement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_key", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
    )
    op.create_index("ix_announcement_files_announcement_id", "announcement_files", ["announcement_id"])

    # --- assignments ---
    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", postgresql.ENUM("individual", "group", name="assignment_type", create_type=False), nullable=False),
        sa.Column("grade_type", postgresql.ENUM("0-5", "0-100", "0-1", name="grade_type", create_type=False), nullable=False),
        sa.Column("grading_type", postgresql.ENUM("uniform", "individual", name="grading_type", create_type=False), nullable=True),
        sa.Column("group_count", sa.Integer(), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_assignments_class_id", "assignments", ["class_id"])

    # --- assignment_materials ---
    op.create_table(
        "assignment_materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("material_type", postgresql.ENUM("link", "file", name="material_type", create_type=False), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("file_key", sa.String(500), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
    )
    op.create_index("ix_assignment_materials_assignment_id", "assignment_materials", ["assignment_id"])

    # --- groups ---
    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
    )
    op.create_index("ix_groups_assignment_id", "groups", ["assignment_id"])

    # --- group_members ---
    op.create_table(
        "group_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_members_group_user"),
    )
    op.create_index("ix_group_members_group_id", "group_members", ["group_id"])

    # --- solutions ---
    op.create_table(
        "solutions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id", ondelete="SET NULL"), nullable=True),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM("created", "submitted", "returned", "graded", "pending_redistribution", name="solution_status", create_type=False), nullable=False, server_default="created"),
        sa.Column("grade", sa.Numeric(5, 2), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_solutions_assignment_id", "solutions", ["assignment_id"])
    op.create_index("ix_solutions_group_id", "solutions", ["group_id"])
    op.create_index("ix_solutions_creator_id", "solutions", ["creator_id"])

    # --- solution_files ---
    op.create_table(
        "solution_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("solution_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_key", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
    )
    op.create_index("ix_solution_files_solution_id", "solution_files", ["solution_id"])

    # --- grade_redistributions ---
    op.create_table(
        "grade_redistributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("solution_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("grade", sa.Numeric(5, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("solution_id", "user_id", name="uq_grade_redis_solution_user"),
    )
    op.create_index("ix_grade_redistributions_solution_id", "grade_redistributions", ["solution_id"])

    # --- refresh_tokens ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # --- notifications ---
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_read", "notifications", ["read"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("refresh_tokens")
    op.drop_table("grade_redistributions")
    op.drop_table("solution_files")
    op.drop_table("solutions")
    op.drop_table("group_members")
    op.drop_table("groups")
    op.drop_table("assignment_materials")
    op.drop_table("assignments")
    op.drop_table("announcement_files")
    op.drop_table("announcements")
    op.drop_table("class_members")
    op.drop_table("classes")
    op.drop_table("users")

    op.execute("DROP TYPE solution_status")
    op.execute("DROP TYPE material_type")
    op.execute("DROP TYPE grading_type")
    op.execute("DROP TYPE grade_type")
    op.execute("DROP TYPE assignment_type")
    op.execute("DROP TYPE member_role")
    op.execute("DROP TYPE class_type")
