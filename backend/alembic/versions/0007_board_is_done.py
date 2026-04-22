"""tenant: add is_done_column to board_columns

Revision ID: 0007_tenant
Revises: 0006_tenant
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa
import os

revision = "0007_tenant"
down_revision = "0006_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.add_column(
        "board_columns",
        sa.Column("is_done_column", sa.Boolean, server_default="false"),
        schema=schema,
    )


def downgrade() -> None:
    schema = os.environ.get("TENANT_SCHEMA", "public")
    op.drop_column("board_columns", "is_done_column", schema=schema)
