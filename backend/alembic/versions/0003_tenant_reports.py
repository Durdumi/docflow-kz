"""tenant: add reports table

Revision ID: 0003_tenant
Revises: 0002_tenant
Create Date: 2026-04-21
"""
import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0003_tenant"
down_revision = "0002_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.create_table(
        "reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("format", sa.String(20), nullable=False, server_default="pdf"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("period_from", sa.DateTime(timezone=True)),
        sa.Column("period_to", sa.DateTime(timezone=True)),
        sa.Column("parameters", JSONB, server_default="{}"),
        sa.Column("result_data", JSONB, server_default="{}"),
        sa.Column("file_url", sa.Text),
        sa.Column("file_size", sa.Integer),
        sa.Column("error_message", sa.Text),
        sa.Column("created_by_id", UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        schema=schema,
    )
    op.create_index("ix_reports_org_id", "reports", ["organization_id"], schema=schema)
    op.create_index("ix_reports_status", "reports", ["status"], schema=schema)


def downgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.drop_index("ix_reports_status", table_name="reports", schema=schema)
    op.drop_index("ix_reports_org_id", table_name="reports", schema=schema)
    op.drop_table("reports", schema=schema)
