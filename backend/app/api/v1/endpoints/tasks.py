import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import CurrentUser, get_db
from app.models.auth import Organization
from app.schemas.tasks import (
    CalendarEventCreate, CalendarEventRead, CalendarEventUpdate,
    TaskCreate, TaskRead, TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])
calendar_router = APIRouter(prefix="/calendar", tags=["Calendar"])


async def _get_schema(current_user: CurrentUser, db: AsyncSession) -> str:
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Нет организации")
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    return org.schema_name


# ─── Tasks ────────────────────────────────────────────────────
@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    service = TaskService(db)
    return await service.create_task(data, current_user.id, current_user.organization_id)


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = None,
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    service = TaskService(db)
    return await service.get_tasks(current_user.organization_id, status_filter)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    service = TaskService(db)
    task = await service.update_task(task_id, data, current_user.organization_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    service = TaskService(db)
    if not await service.delete_task(task_id, current_user.organization_id):
        raise HTTPException(status_code=404, detail="Задача не найдена")


# ─── Calendar ─────────────────────────────────────────────────
@calendar_router.post("", response_model=CalendarEventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: CalendarEventCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    service = TaskService(db)
    return await service.create_event(data, current_user.id, current_user.organization_id)


@calendar_router.get("", response_model=list[CalendarEventRead])
async def list_events(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    year: int | None = None,
    month: int | None = None,
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    service = TaskService(db)
    return await service.get_events(current_user.organization_id, year, month)


@calendar_router.patch("/{event_id}", response_model=CalendarEventRead)
async def update_event(
    event_id: uuid.UUID,
    data: CalendarEventUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    service = TaskService(db)
    event = await service.update_event(event_id, data, current_user.organization_id)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event


@calendar_router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    service = TaskService(db)
    if not await service.delete_event(event_id, current_user.organization_id):
        raise HTTPException(status_code=404, detail="Событие не найдено")
