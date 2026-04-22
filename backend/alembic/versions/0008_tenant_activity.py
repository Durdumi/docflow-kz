"""tenant: task_activities table

Revision ID: 0008_tenant
Revises: 0007_tenant
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
import os

revision = "0008_tenant"
down_revision = "0007_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.create_table(
        "task_activities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), nullable=False),
        sa.Column("actor_name", sa.String(255), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("field_name", sa.String(100)),
        sa.Column("old_value", sa.Text),
        sa.Column("new_value", sa.Text),
        sa.Column("meta", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_task_activities_task_id", "task_activities", ["task_id"], schema=schema)
    op.create_index("ix_task_activities_org_id", "task_activities", ["organization_id"], schema=schema)


def downgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.drop_index("ix_task_activities_org_id", table_name="task_activities", schema=schema)
    op.drop_index("ix_task_activities_task_id", table_name="task_activities", schema=schema)
    op.drop_table("task_activities", schema=schema)
