import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.v1.deps import AdminUser, CurrentUser, ManagerUser, TenantDB
from app.models.documents import DocumentStatus, TemplateCategory
from app.schemas.documents import (
    DocumentCreate,
    DocumentRead,
    DocumentStatusUpdate,
    DocumentTemplateCreate,
    DocumentTemplateRead,
    DocumentTemplateShort,
    DocumentTemplateUpdate,
    DocumentUpdate,
    PaginatedDocuments,
    PaginatedTemplates,
)
from app.services.document_service import DocumentError, DocumentService

templates_router = APIRouter(prefix="/templates", tags=["Templates"])
documents_router = APIRouter(prefix="/documents", tags=["Documents"])


def _svc(db: TenantDB) -> DocumentService:
    return DocumentService(db)


# ═══════════════════════════════════════════════════════════════════════════════
# Templates
# ═══════════════════════════════════════════════════════════════════════════════


@templates_router.get("", response_model=PaginatedTemplates)
async def list_templates(
    db: TenantDB,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: TemplateCategory | None = None,
    search: str | None = Query(None, max_length=255),
    active_only: bool = True,
    _: CurrentUser = None,
):
    return await _svc(db).list_templates(
        page=page,
        page_size=page_size,
        category=category.value if category else None,
        search=search,
        active_only=active_only,
    )


@templates_router.get("/all-short", response_model=list[DocumentTemplateShort])
async def list_templates_short(
    db: TenantDB,
    _: CurrentUser = None,
):
    """Краткий список активных шаблонов для select/dropdown."""
    result = await _svc(db).list_templates(page=1, page_size=200, active_only=True)
    return result.items


@templates_router.get("/{template_id}", response_model=DocumentTemplateRead)
async def get_template(
    template_id: uuid.UUID,
    db: TenantDB,
    _: CurrentUser = None,
):
    try:
        template = await _svc(db).get_template(template_id)
        return DocumentTemplateRead.model_validate(template)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@templates_router.post("", response_model=DocumentTemplateRead, status_code=201)
async def create_template(
    data: DocumentTemplateCreate,
    db: TenantDB,
    current_user: ManagerUser,
):
    try:
        return await _svc(db).create_template(data, current_user.id)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@templates_router.put("/{template_id}", response_model=DocumentTemplateRead)
async def update_template(
    template_id: uuid.UUID,
    data: DocumentTemplateUpdate,
    db: TenantDB,
    _: ManagerUser,
):
    try:
        return await _svc(db).update_template(template_id, data)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@templates_router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    db: TenantDB,
    _: AdminUser,
):
    try:
        await _svc(db).delete_template(template_id)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ═══════════════════════════════════════════════════════════════════════════════
# Documents
# ═══════════════════════════════════════════════════════════════════════════════


@documents_router.get("", response_model=PaginatedDocuments)
async def list_documents(
    db: TenantDB,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: DocumentStatus | None = None,
    template_id: uuid.UUID | None = None,
    search: str | None = Query(None, max_length=255),
    my_only: bool = False,
):
    return await _svc(db).list_documents(
        page=page,
        page_size=page_size,
        status=status.value if status else None,
        template_id=template_id,
        search=search,
        created_by_id=current_user.id if my_only else None,
    )


@documents_router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID,
    db: TenantDB,
    _: CurrentUser,
):
    try:
        doc = await _svc(db).get_document(document_id)
        return DocumentRead.model_validate(doc)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@documents_router.post("", response_model=DocumentRead, status_code=201)
async def create_document(
    data: DocumentCreate,
    db: TenantDB,
    current_user: CurrentUser,
):
    try:
        return await _svc(db).create_document(data, current_user.id)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@documents_router.put("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: uuid.UUID,
    data: DocumentUpdate,
    db: TenantDB,
    _: CurrentUser,
):
    try:
        return await _svc(db).update_document(document_id, data)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@documents_router.patch("/{document_id}/status", response_model=DocumentRead)
async def update_document_status(
    document_id: uuid.UUID,
    data: DocumentStatusUpdate,
    db: TenantDB,
    _: ManagerUser,
):
    try:
        return await _svc(db).update_document_status(document_id, data.status)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@documents_router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    db: TenantDB,
    _: CurrentUser,
):
    try:
        await _svc(db).delete_document(document_id)
    except DocumentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
