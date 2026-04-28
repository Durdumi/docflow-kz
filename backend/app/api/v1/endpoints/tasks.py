import uuid
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import CurrentUser, get_db
from app.models.auth import Organization, User
from app.models.tasks import Task
from app.schemas.tasks import (
    CalendarEventCreate, CalendarEventRead, CalendarEventUpdate,
    TaskCreate, TaskRead, TaskUpdate,
)
from app.services.activity_service import ActivityService
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


async def _notify_users(task: Task, text_msg: str, db: AsyncSession, exclude_id: uuid.UUID | None = None):
    """Send Telegram to assignee and creator, excluding actor."""
    from app.services.telegram_service import send_message

    notify_ids: set[uuid.UUID] = set()
    if task.assignee_id:
        notify_ids.add(task.assignee_id)
    if task.created_by_id:
        notify_ids.add(task.created_by_id)
    if exclude_id:
        notify_ids.discard(exclude_id)
    if not notify_ids:
        return

    await db.execute(text("SET search_path TO public"))
    for uid in notify_ids:
        try:
            r = await db.execute(select(User).where(User.id == uid))
            u = r.scalar_one_or_none()
            if u and u.telegram_chat_id:
                await send_message(u.telegram_chat_id, text_msg)
        except Exception as e:
            print(f"[Notify] Error for {uid}: {e}")


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
    activity_svc = ActivityService(db)

    task = await service.create_task(data, current_user.id, current_user.organization_id)

    result = await db.execute(select(Task).where(Task.id == task.id))
    task_obj = result.scalar_one()

    activity = await activity_svc.log(
        task=task_obj,
        actor=current_user,
        action="created",
        meta={"title": str(task.title), "priority": str(task.priority)},
    )
    await db.commit()

    # Notify assignee (including self-assignment)
    if task.assignee_id:
        await db.execute(text("SET search_path TO public"))
        assignee_result = await db.execute(select(User).where(User.id == task.assignee_id))
        assignee = assignee_result.scalar_one_or_none()
        if assignee and assignee.telegram_chat_id:
            from app.services.telegram_service import send_message
            priority_emoji = {"low": "↓", "medium": "→", "high": "↑", "urgent": "🔥"}.get(str(task.priority), "→")
            due_text = f"\n📅 Дедлайн: {task.due_date.strftime('%d.%m.%Y')}" if task.due_date else ""
            assigned_by = "" if assignee.id == current_user.id else f"\n\nНазначил: {current_user.last_name} {current_user.first_name}"
            msg = (
                f"📌 Вам назначена задача!\n\n"
                f"<b>{task.title}</b>\n"
                f"{priority_emoji} Приоритет: {task.priority}{due_text}{assigned_by}"
            )
            await send_message(assignee.telegram_chat_id, msg)

    return task


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = None,
    board_id: uuid.UUID | None = None,
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    service = TaskService(db)
    return await service.get_tasks(current_user.organization_id, status_filter, board_id)


@router.get("/{task_id}/activity")
async def get_task_activity(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    activity_svc = ActivityService(db)
    activities = await activity_svc.get_task_history(task_id, current_user.organization_id)
    return [
        {
            "id": str(a.id),
            "actor_name": a.actor_name,
            "action": a.action,
            "field_name": a.field_name,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "created_at": a.created_at.isoformat(),
        }
        for a in activities
    ]


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))

    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.organization_id == current_user.organization_id)
    )
    task_obj = result.scalar_one_or_none()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    activity_svc = ActivityService(db)
    update_data = data.model_dump(exclude_unset=True)
    activities_to_log: list[dict] = []
    direct_notifications: list[tuple[str, str]] = []

    if "status" in update_data and update_data["status"] != task_obj.status:
        new_status = update_data["status"]
        activities_to_log.append({
            "action": "completed" if new_status == "done" else "status_changed",
            "field_name": "status",
            "old_value": task_obj.status,
            "new_value": new_status,
        })

    if "assignee_id" in update_data and update_data["assignee_id"] != str(task_obj.assignee_id) if task_obj.assignee_id else update_data["assignee_id"] is not None:
        old_name = "никто"
        new_name = "никто"
        await db.execute(text("SET search_path TO public"))
        if task_obj.assignee_id:
            r = await db.execute(select(User).where(User.id == task_obj.assignee_id))
            u = r.scalar_one_or_none()
            if u:
                old_name = f"{u.last_name} {u.first_name}"
        new_assignee_id = update_data["assignee_id"]
        if new_assignee_id:
            r = await db.execute(select(User).where(User.id == new_assignee_id))
            u = r.scalar_one_or_none()
            if u:
                new_name = f"{u.last_name} {u.first_name}"
                if u.telegram_chat_id and u.id != current_user.id:
                    direct_notifications.append((
                        u.telegram_chat_id,
                        f"👤 Вам назначена задача <b>{task_obj.title}</b>\nНазначил: {current_user.last_name} {current_user.first_name}",
                    ))
        await db.execute(text(f'SET search_path TO "{schema}", public'))
        activities_to_log.append({
            "action": "assignee_changed",
            "field_name": "assignee_id",
            "old_value": old_name,
            "new_value": new_name,
        })

    if "priority" in update_data and update_data["priority"] != task_obj.priority:
        activities_to_log.append({
            "action": "priority_changed",
            "field_name": "priority",
            "old_value": str(task_obj.priority),
            "new_value": str(update_data["priority"]),
        })

    if "title" in update_data and update_data["title"] != task_obj.title:
        activities_to_log.append({
            "action": "title_changed",
            "field_name": "title",
            "old_value": task_obj.title,
            "new_value": update_data["title"],
        })

    if "due_date" in update_data:
        old_due = task_obj.due_date.strftime("%d.%m.%Y") if task_obj.due_date else "не задан"
        new_due = update_data["due_date"]
        if new_due:
            if isinstance(new_due, str):
                new_due = datetime.fromisoformat(new_due.replace("Z", "+00:00"))
            new_due_str = new_due.strftime("%d.%m.%Y") if hasattr(new_due, "strftime") else str(new_due)
        else:
            new_due_str = "не задан"
        if old_due != new_due_str:
            activities_to_log.append({
                "action": "due_date_changed",
                "field_name": "due_date",
                "old_value": old_due,
                "new_value": new_due_str,
            })

    if "description" in update_data and update_data["description"] != task_obj.description:
        activities_to_log.append({
            "action": "description_changed",
            "field_name": "description",
            "old_value": None,
            "new_value": None,
        })

    service = TaskService(db)
    task = await service.update_task(task_id, data, current_user.organization_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    result2 = await db.execute(select(Task).where(Task.id == task_id))
    task_obj_updated = result2.scalar_one()

    for act_data in activities_to_log:
        activity = await activity_svc.log(task=task_obj_updated, actor=current_user, **act_data)
        text_msg = activity_svc.format_activity_message(activity, task_obj_updated.title)
        await _notify_users(task_obj_updated, text_msg, db, exclude_id=current_user.id)
        await db.execute(text(f'SET search_path TO "{schema}", public'))

    await db.commit()

    from app.services.telegram_service import send_message
    for chat_id, msg in direct_notifications:
        try:
            await send_message(chat_id, msg)
        except Exception as e:
            print(f"[Notify] Direct error: {e}")

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
