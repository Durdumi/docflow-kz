"""tenant: add tasks and calendar_events tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import os

revision = "0005_tenant"
down_revision = "0004_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")

    op.create_table(
        "tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(50), nullable=False, server_default="todo"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("assignee_id", UUID(as_uuid=True)),
        sa.Column("created_by_id", UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("related_document_id", UUID(as_uuid=True)),
        sa.Column("related_report_id", UUID(as_uuid=True)),
        sa.Column("position", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_tasks_org_id", "tasks", ["organization_id"], schema=schema)
    op.create_index("ix_tasks_status", "tasks", ["status"], schema=schema)
    op.create_index("ix_tasks_assignee", "tasks", ["assignee_id"], schema=schema)

    op.create_table(
        "calendar_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("color", sa.String(20), server_default="#1677ff"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True)),
        sa.Column("all_day", sa.Boolean, server_default="true"),
        sa.Column("event_type", sa.String(50), server_default="custom"),
        sa.Column("related_document_id", UUID(as_uuid=True)),
        sa.Column("related_report_id", UUID(as_uuid=True)),
        sa.Column("related_task_id", UUID(as_uuid=True)),
        sa.Column("created_by_id", UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index("ix_calendar_org_id", "calendar_events", ["organization_id"], schema=schema)
    op.create_index("ix_calendar_start", "calendar_events", ["start_date"], schema=schema)


def downgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.drop_table("calendar_events", schema=schema)
    op.drop_table("tasks", schema=schema)
