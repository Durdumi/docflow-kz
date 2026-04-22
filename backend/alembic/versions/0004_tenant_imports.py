"""tenant: add data_imports table

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
import os

revision = "0004_tenant"
down_revision = "0003_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.create_table(
        "data_imports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("file_url", sa.Text),
        sa.Column("row_count", sa.Integer, server_default="0"),
        sa.Column("columns", JSONB, server_default="[]"),
        sa.Column("preview_data", JSONB, server_default="[]"),
        sa.Column("imported_data", JSONB, server_default="[]"),
        sa.Column("error_message", sa.Text),
        sa.Column("created_by_id", UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index(
        "ix_imports_org_id", "data_imports", ["organization_id"], schema=schema
    )


def downgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.drop_index("ix_imports_org_id", table_name="data_imports", schema=schema)
    op.drop_table("data_imports", schema=schema)
