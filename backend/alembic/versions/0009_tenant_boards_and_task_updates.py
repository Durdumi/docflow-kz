"""tenant: boards table + task rich fields

Revision ID: 0009_tenant
Revises: 0008_tenant
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
import os

revision = "0009_tenant"
down_revision = "0008_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")

    op.create_table(
        "boards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("color", sa.String(20), server_default="#1677ff"),
        sa.Column("is_archived", sa.Boolean, server_default="false"),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_boards_org_id", "boards", ["organization_id"], schema=schema)

    for col_name in [
        ("board_id",        UUID(as_uuid=True), {}),
        ("assignee_ids",    JSONB,              {"server_default": "[]"}),
        ("checklist",       JSONB,              {"server_default": "[]"}),
        ("attachments",     JSONB,              {"server_default": "[]"}),
        ("comments",        JSONB,              {"server_default": "[]"}),
        ("cover_color",     sa.String(20),      {}),
        ("label_ids",       JSONB,              {"server_default": "[]"}),
        ("watch_user_ids",  JSONB,              {"server_default": "[]"}),
    ]:
        name, col_type, kwargs = col_name
        op.add_column(
            "tasks",
            sa.Column(name, col_type, **kwargs),
            schema=schema,
        )


def downgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.drop_index("ix_boards_org_id", "boards", schema=schema)
    op.drop_table("boards", schema=schema)
    for col in ["board_id", "assignee_ids", "checklist", "attachments",
                "comments", "cover_color", "label_ids", "watch_user_ids"]:
        op.drop_column("tasks", col, schema=schema)
