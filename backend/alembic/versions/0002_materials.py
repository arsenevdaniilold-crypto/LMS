"""class materials

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- materials ---
    op.create_table(
        "materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_materials_class_id", "materials", ["class_id"])

    # --- material_items (reuse existing material_type enum) ---
    op.create_table(
        "material_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("material_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_type", postgresql.ENUM("link", "file", name="material_type", create_type=False), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("file_key", sa.String(500), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_material_items_material_id", "material_items", ["material_id"])


def downgrade() -> None:
    op.drop_table("material_items")
    op.drop_table("materials")
