import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.documents import DocumentStatus, TemplateCategory

# ─── Template Field ───────────────────────────────────────────────────────────
FieldType = Literal["text", "number", "date", "select", "textarea", "checkbox"]


class TemplateField(BaseModel):
    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=255)
    type: FieldType
    required: bool = False
    options: list[str] | None = None  # для type=select
    default_value: str | None = None


# ─── DocumentTemplate Schemas ─────────────────────────────────────────────────
class DocumentTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    category: TemplateCategory = TemplateCategory.OTHER
    fields: list[TemplateField] = Field(default_factory=list)


class DocumentTemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: TemplateCategory | None = None
    fields: list[TemplateField] | None = None
    is_active: bool | None = None


class DocumentTemplateRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    description: str | None
    category: str
    fields: list[dict[str, Any]]
    is_active: bool
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DocumentTemplateShort(BaseModel):
    """Краткое представление для select/dropdown."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    category: str
    fields: list[dict[str, Any]]


# ─── Document Schemas ─────────────────────────────────────────────────────────
class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    template_id: uuid.UUID | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    status: DocumentStatus = DocumentStatus.DRAFT


class DocumentUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    data: dict[str, Any] | None = None


class DocumentStatusUpdate(BaseModel):
    status: DocumentStatus


class DocumentRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    template_id: uuid.UUID | None
    data: dict[str, Any]
    status: str
    file_url: str | None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ─── Pagination ───────────────────────────────────────────────────────────────
class PaginatedTemplates(BaseModel):
    items: list[DocumentTemplateRead]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedDocuments(BaseModel):
    items: list[DocumentRead]
    total: int
    page: int
    page_size: int
    pages: int
