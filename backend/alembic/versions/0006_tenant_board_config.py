"""tenant: board_columns, label_colors, tasks.label_color

Revision ID: 0006_tenant
Revises: 0005_tenant
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import os

revision = "0006_tenant"
down_revision = "0005_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")

    op.create_table(
        "board_columns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(50), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("color", sa.String(20), server_default="#f5f5f5"),
        sa.Column("position", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_board_columns_org", "board_columns", ["organization_id"], schema=schema)

    op.create_table(
        "label_colors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("color", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_label_colors_org", "label_colors", ["organization_id"], schema=schema)

    op.add_column("tasks", sa.Column("label_color", sa.String(20)), schema=schema)


def downgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.drop_column("tasks", "label_color", schema=schema)
    op.drop_table("label_colors", schema=schema)
    op.drop_table("board_columns", schema=schema)
