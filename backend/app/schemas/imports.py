import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.imports import ImportSourceType, ImportStatus


class DataImportRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    category: str | None
    source_type: ImportSourceType
    status: ImportStatus
    original_filename: str
    row_count: int
    columns: list
    preview_data: list
    error_message: str | None
    created_by_id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DataImportListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    category: str | None
    source_type: ImportSourceType
    status: ImportStatus
    original_filename: str
    row_count: int
    columns: list
    created_at: datetime
