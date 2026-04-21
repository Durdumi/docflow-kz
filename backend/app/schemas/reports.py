import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.reports import ReportFormat, ReportStatus, ReportType


class ReportCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: ReportType
    format: ReportFormat = ReportFormat.PDF
    period_from: datetime | None = None
    period_to: datetime | None = None
    parameters: dict = Field(default_factory=dict)


class ReportRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    type: ReportType
    format: ReportFormat
    status: ReportStatus
    period_from: datetime | None
    period_to: datetime | None
    parameters: dict
    file_url: str | None
    file_size: int | None
    error_message: str | None
    created_by_id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class ReportListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    type: ReportType
    format: ReportFormat
    status: ReportStatus
    period_from: datetime | None
    period_to: datetime | None
    file_url: str | None
    created_at: datetime
    completed_at: datetime | None
