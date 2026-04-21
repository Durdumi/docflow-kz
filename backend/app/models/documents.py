"""
Модели TENANT схемы — хранятся в schema каждой организации (org_{slug}).
Не имеют FK на public schema — только UUID-ссылки.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import TenantBase


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TemplateCategory(str, Enum):
    CONTRACT = "contract"       # Договоры
    ACT = "act"                 # Акты
    INVOICE = "invoice"         # Счета / накладные
    REPORT = "report"           # Отчёты
    ORDER = "order"             # Приказы / распоряжения
    APPLICATION = "application" # Заявления
    OTHER = "other"             # Прочее


# ─── Mixins ───────────────────────────────────────────────────────────────────
class TenantTimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantUUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


# ─── DocumentTemplate ─────────────────────────────────────────────────────────
class DocumentTemplate(TenantUUIDMixin, TenantTimestampMixin, TenantBase):
    """
    Шаблон документа организации.
    fields — список TemplateField (JSONB), описывает форму заполнения.
    """
    __tablename__ = "document_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default=TemplateCategory.OTHER, nullable=False)

    # Список полей: [{id, name, label, type, required, options?, default_value?}]
    fields: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # UUID пользователя из public.users (нет FK — кросс-схемная ссылка)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    def __repr__(self) -> str:
        return f"<DocumentTemplate {self.name}>"


# ─── Document ─────────────────────────────────────────────────────────────────
class Document(TenantUUIDMixin, TenantTimestampMixin, TenantBase):
    """
    Заполненный (или черновой) документ.
    data — значения полей шаблона (JSONB).
    """
    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # UUID шаблона внутри той же схемы (нет FK — опциональная ссылка)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)

    # Заполненные данные: {field_name: value}
    data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    status: Mapped[str] = mapped_column(
        String(50), default=DocumentStatus.DRAFT, nullable=False, index=True
    )

    # Путь к файлу в MinIO (появляется после генерации PDF/DOCX)
    file_url: Mapped[str | None] = mapped_column(Text)

    # UUID пользователя из public.users
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Document {self.title} [{self.status}]>"
