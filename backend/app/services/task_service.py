import uuid
from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tasks import CalendarEvent, Task, TaskStatus
from app.schemas.tasks import (
    CalendarEventCreate, CalendarEventRead, CalendarEventUpdate,
    TaskCreate, TaskRead, TaskUpdate,
)


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Tasks ────────────────────────────────────────────────
    async def create_task(
        self, data: TaskCreate, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> TaskRead:
        task = Task(
            **data.model_dump(),
            created_by_id=user_id,
            organization_id=org_id,
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        await self.db.commit()
        return TaskRead.model_validate(task)

    async def get_tasks(
        self, org_id: uuid.UUID, status: str | None = None, board_id: uuid.UUID | None = None
    ) -> list[TaskRead]:
        query = select(Task).where(Task.organization_id == org_id)
        if status:
            query = query.where(Task.status == status)
        if board_id:
            query = query.where(Task.board_id == board_id)
        query = query.order_by(Task.position, Task.created_at)
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        return [TaskRead.model_validate(t) for t in tasks]

    async def get_task(self, task_id: uuid.UUID, org_id: uuid.UUID) -> TaskRead | None:
        result = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.organization_id == org_id)
        )
        task = result.scalar_one_or_none()
        return TaskRead.model_validate(task) if task else None

    async def update_task(
        self, task_id: uuid.UUID, data: TaskUpdate, org_id: uuid.UUID
    ) -> TaskRead | None:
        result = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.organization_id == org_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if update_data.get("status") == TaskStatus.DONE and task.status != TaskStatus.DONE:
            task.completed_at = datetime.now(UTC)
        elif update_data.get("status") and update_data["status"] != TaskStatus.DONE:
            task.completed_at = None

        for field, value in update_data.items():
            setattr(task, field, value)

        await self.db.commit()
        await self.db.refresh(task)
        return TaskRead.model_validate(task)

    async def delete_task(self, task_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.organization_id == org_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return False
        await self.db.delete(task)
        await self.db.commit()
        return True

    # ─── Calendar Events ──────────────────────────────────────
    async def create_event(
        self, data: CalendarEventCreate, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> CalendarEventRead:
        event = CalendarEvent(
            **data.model_dump(),
            created_by_id=user_id,
            organization_id=org_id,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        await self.db.commit()
        return CalendarEventRead.model_validate(event)

    async def get_events(
        self,
        org_id: uuid.UUID,
        year: int | None = None,
        month: int | None = None,
    ) -> list[CalendarEventRead]:
        query = select(CalendarEvent).where(CalendarEvent.organization_id == org_id)
        if year and month:
            from sqlalchemy import extract
            query = query.where(
                extract("year", CalendarEvent.start_date) == year,
                extract("month", CalendarEvent.start_date) == month,
            )
        query = query.order_by(CalendarEvent.start_date)
        result = await self.db.execute(query)
        events = result.scalars().all()
        return [CalendarEventRead.model_validate(e) for e in events]

    async def update_event(
        self, event_id: uuid.UUID, data: CalendarEventUpdate, org_id: uuid.UUID
    ) -> CalendarEventRead | None:
        result = await self.db.execute(
            select(CalendarEvent).where(
                CalendarEvent.id == event_id,
                CalendarEvent.organization_id == org_id,
            )
        )
        event = result.scalar_one_or_none()
        if not event:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(event, field, value)
        await self.db.commit()
        await self.db.refresh(event)
        return CalendarEventRead.model_validate(event)

    async def delete_event(self, event_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(CalendarEvent).where(
                CalendarEvent.id == event_id,
                CalendarEvent.organization_id == org_id,
            )
        )
        event = result.scalar_one_or_none()
        if not event:
            return False
        await self.db.delete(event)
        await self.db.commit()
        return True
