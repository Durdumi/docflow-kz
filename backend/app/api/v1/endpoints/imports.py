import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.api.v1.deps import CurrentUser, get_db
from app.models.auth import Organization
from app.schemas.imports import DataImportListItem, DataImportRead
from app.services.import_service import ImportService

router = APIRouter(prefix="/imports", tags=["Imports"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def _get_schema(current_user: CurrentUser, db: AsyncSession) -> str:
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Пользователь не привязан к организации")
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    return org.schema_name


@router.post("", response_model=DataImportRead, status_code=status.HTTP_201_CREATED)
async def upload_import(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str | None = Form(None),
):
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 10 MB)")

    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("xlsx", "xls", "csv", "json"):
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только файлы: .xlsx, .xls, .csv, .json",
        )

    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))

    try:
        return await ImportService(db).create_from_file(
            file_bytes=file_bytes,
            filename=filename,
            name=name,
            category=category,
            user_id=current_user.id,
            org_id=current_user.organization_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при импорте: {str(e)}")


@router.get("", response_model=dict)
async def list_imports(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    return await ImportService(db).get_list(current_user.organization_id, page, page_size)


@router.get("/{import_id}", response_model=DataImportRead)
async def get_import(
    import_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    record = await ImportService(db).get_by_id(import_id, current_user.organization_id)
    if not record:
        raise HTTPException(status_code=404, detail="Импорт не найден")
    return record


@router.delete("/{import_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_import(
    import_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    deleted = await ImportService(db).delete(import_id, current_user.organization_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Импорт не найден")
