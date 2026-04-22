from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import TenantBase


class ImportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class ImportSourceType(str, Enum):
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class DataImport(TenantBase):
    __tablename__ = "data_imports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    source_type: Mapped[ImportSourceType] = mapped_column(String(20), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(String(50), default=ImportStatus.PENDING)

    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_url: Mapped[str | None] = mapped_column(Text)

    row_count: Mapped[int] = mapped_column(Integer, default=0)
    columns: Mapped[list] = mapped_column(JSONB, default=list)
    preview_data: Mapped[list] = mapped_column(JSONB, default=list)
    imported_data: Mapped[list] = mapped_column(JSONB, default=list)

    error_message: Mapped[str | None] = mapped_column(Text)

    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
