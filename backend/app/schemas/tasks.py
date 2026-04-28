import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.tasks import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None
    assignee_id: uuid.UUID | None = None
    related_document_id: uuid.UUID | None = None
    related_report_id: uuid.UUID | None = None
    position: int = 0
    label_color: str | None = None
    board_id: uuid.UUID | None = None
    assignee_ids: list[uuid.UUID] = Field(default_factory=list)
    checklist: list[dict] = Field(default_factory=list)
    cover_color: str | None = None
    label_ids: list[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assignee_id: uuid.UUID | None = None
    position: int | None = None
    label_color: str | None = None
    board_id: uuid.UUID | None = None
    assignee_ids: list[uuid.UUID] | None = None
    checklist: list[dict] | None = None
    attachments: list[dict] | None = None
    comments: list[dict] | None = None
    cover_color: str | None = None
    label_ids: list[str] | None = None
    watch_user_ids: list[str] | None = None


class TaskRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    completed_at: datetime | None
    assignee_id: uuid.UUID | None
    created_by_id: uuid.UUID
    organization_id: uuid.UUID
    related_document_id: uuid.UUID | None
    related_report_id: uuid.UUID | None
    position: int
    label_color: str | None
    created_at: datetime
    updated_at: datetime
    board_id: uuid.UUID | None = None
    assignee_ids: list = Field(default_factory=list)
    checklist: list = Field(default_factory=list)
    attachments: list = Field(default_factory=list)
    comments: list = Field(default_factory=list)
    cover_color: str | None = None
    label_ids: list = Field(default_factory=list)
    watch_user_ids: list = Field(default_factory=list)


class CalendarEventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    color: str = "#1677ff"
    start_date: datetime
    end_date: datetime | None = None
    all_day: bool = True
    event_type: str = "custom"
    related_document_id: uuid.UUID | None = None
    related_report_id: uuid.UUID | None = None
    related_task_id: uuid.UUID | None = None


class CalendarEventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    color: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    all_day: bool | None = None


class CalendarEventRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    description: str | None
    color: str
    start_date: datetime
    end_date: datetime | None
    all_day: bool
    event_type: str
    related_document_id: uuid.UUID | None
    related_report_id: uuid.UUID | None
    related_task_id: uuid.UUID | None
    created_by_id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
