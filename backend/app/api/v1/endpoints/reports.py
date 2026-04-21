import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser, get_db
from app.models.auth import Organization
from app.schemas.reports import ReportCreate, ReportListItem, ReportRead
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


async def _get_schema(current_user: CurrentUser, db: AsyncSession) -> str:
    """Загружает реальный schema_name организации из public.organizations."""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Пользователь не привязан к организации")
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    return org.schema_name


@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(
    data: ReportCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET LOCAL search_path TO "{schema}", public'))
    return await ReportService(db, schema).create(data, current_user.id, current_user.organization_id)


@router.get("", response_model=dict)
async def list_reports(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET LOCAL search_path TO "{schema}", public'))
    return await ReportService(db, schema).get_list(current_user.organization_id, page, page_size)


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET LOCAL search_path TO "{schema}", public'))
    report = await ReportService(db, schema).get_by_id(report_id, current_user.organization_id)
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET LOCAL search_path TO "{schema}", public'))
    deleted = await ReportService(db, schema).delete(report_id, current_user.organization_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
