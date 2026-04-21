import math
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.documents import Document, DocumentStatus, DocumentTemplate
from app.schemas.documents import (
    DocumentCreate,
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
    DocumentUpdate,
    PaginatedDocuments,
    PaginatedTemplates,
    DocumentRead,
    DocumentTemplateRead,
)


class DocumentError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════════════════════════
    # Templates
    # ═══════════════════════════════════════════════════════════════

    async def list_templates(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        search: str | None = None,
        active_only: bool = True,
    ) -> PaginatedTemplates:
        query = select(DocumentTemplate)

        if active_only:
            query = query.where(DocumentTemplate.is_active == True)  # noqa: E712
        if category:
            query = query.where(DocumentTemplate.category == category)
        if search:
            query = query.where(DocumentTemplate.name.ilike(f"%{search}%"))

        # Считаем total
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        # Данные страницы
        offset = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(DocumentTemplate.created_at.desc()).offset(offset).limit(page_size)
        )
        templates = result.scalars().all()

        return PaginatedTemplates(
            items=[DocumentTemplateRead.model_validate(t) for t in templates],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )

    async def get_template(self, template_id: uuid.UUID) -> DocumentTemplate:
        result = await self.db.execute(
            select(DocumentTemplate).where(DocumentTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise DocumentError("Шаблон не найден", status_code=404)
        return template

    async def create_template(
        self, data: DocumentTemplateCreate, created_by_id: uuid.UUID
    ) -> DocumentTemplateRead:
        template = DocumentTemplate(
            name=data.name,
            description=data.description,
            category=data.category.value,
            fields=[f.model_dump() for f in data.fields],
            created_by_id=created_by_id,
        )
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return DocumentTemplateRead.model_validate(template)

    async def update_template(
        self, template_id: uuid.UUID, data: DocumentTemplateUpdate
    ) -> DocumentTemplateRead:
        template = await self.get_template(template_id)

        if data.name is not None:
            template.name = data.name
        if data.description is not None:
            template.description = data.description
        if data.category is not None:
            template.category = data.category.value
        if data.fields is not None:
            template.fields = [f.model_dump() for f in data.fields]
        if data.is_active is not None:
            template.is_active = data.is_active

        await self.db.flush()
        await self.db.refresh(template)
        return DocumentTemplateRead.model_validate(template)

    async def delete_template(self, template_id: uuid.UUID) -> None:
        template = await self.get_template(template_id)
        template.is_active = False
        await self.db.flush()

    # ═══════════════════════════════════════════════════════════════
    # Documents
    # ═══════════════════════════════════════════════════════════════

    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        template_id: uuid.UUID | None = None,
        search: str | None = None,
        created_by_id: uuid.UUID | None = None,
    ) -> PaginatedDocuments:
        query = select(Document).where(Document.status != DocumentStatus.DELETED.value)

        if status:
            query = query.where(Document.status == status)
        if template_id:
            query = query.where(Document.template_id == template_id)
        if search:
            query = query.where(Document.title.ilike(f"%{search}%"))
        if created_by_id:
            query = query.where(Document.created_by_id == created_by_id)

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        offset = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        )
        documents = result.scalars().all()

        return PaginatedDocuments(
            items=[DocumentRead.model_validate(d) for d in documents],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )

    async def get_document(self, document_id: uuid.UUID) -> Document:
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.status != DocumentStatus.DELETED.value,
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise DocumentError("Документ не найден", status_code=404)
        return document

    async def create_document(
        self, data: DocumentCreate, created_by_id: uuid.UUID
    ) -> DocumentRead:
        document = Document(
            title=data.title,
            template_id=data.template_id,
            data=data.data,
            status=data.status.value,
            created_by_id=created_by_id,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return DocumentRead.model_validate(document)

    async def update_document(
        self, document_id: uuid.UUID, data: DocumentUpdate
    ) -> DocumentRead:
        document = await self.get_document(document_id)

        if data.title is not None:
            document.title = data.title
        if data.data is not None:
            document.data = data.data

        await self.db.flush()
        await self.db.refresh(document)
        return DocumentRead.model_validate(document)

    async def update_document_status(
        self, document_id: uuid.UUID, status: DocumentStatus
    ) -> DocumentRead:
        document = await self.get_document(document_id)
        document.status = status.value
        await self.db.flush()
        await self.db.refresh(document)
        return DocumentRead.model_validate(document)

    async def delete_document(self, document_id: uuid.UUID) -> None:
        document = await self.get_document(document_id)
        document.status = DocumentStatus.DELETED.value
        await self.db.flush()
