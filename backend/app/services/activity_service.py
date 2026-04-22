import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity import TaskActivity
from app.models.auth import User
from app.models.tasks import Task


STATUS_LABELS = {
    "todo": "📋 Надо сделать",
    "in_progress": "⚡ В работе",
    "review": "👀 На проверке",
    "done": "✅ Готово",
}

PRIORITY_LABELS = {
    "low": "↓ Низкий",
    "medium": "→ Средний",
    "high": "↑ Высокий",
    "urgent": "🔥 Срочно",
}


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        task: Task,
        actor: User,
        action: str,
        field_name: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        meta: dict | None = None,
    ) -> TaskActivity:
        activity = TaskActivity(
            task_id=task.id,
            organization_id=task.organization_id,
            actor_id=actor.id,
            actor_name=f"{actor.last_name} {actor.first_name}",
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            meta=meta or {},
        )
        self.db.add(activity)
        await self.db.flush()
        return activity

    async def get_task_history(
        self, task_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[TaskActivity]:
        result = await self.db.execute(
            select(TaskActivity)
            .where(
                TaskActivity.task_id == task_id,
                TaskActivity.organization_id == org_id,
            )
            .order_by(TaskActivity.created_at.desc())
            .limit(50)
        )
        return list(result.scalars().all())

    def format_activity_message(self, activity: TaskActivity, task_title: str) -> str:
        actor = activity.actor_name

        if activity.action == "created":
            return f"✨ <b>{actor}</b> создал задачу\n📌 {task_title}"

        if activity.action == "status_changed":
            old = STATUS_LABELS.get(activity.old_value or "", activity.old_value or "—")
            new = STATUS_LABELS.get(activity.new_value or "", activity.new_value or "—")
            return f"🔄 <b>{actor}</b> изменил статус\n📌 {task_title}\n{old} → {new}"

        if activity.action == "assignee_changed":
            old = activity.old_value or "никто"
            new = activity.new_value or "никто"
            return f"👤 <b>{actor}</b> изменил ответственного\n📌 {task_title}\n{old} → {new}"

        if activity.action == "priority_changed":
            old = PRIORITY_LABELS.get(activity.old_value or "", activity.old_value or "—")
            new = PRIORITY_LABELS.get(activity.new_value or "", activity.new_value or "—")
            return f"🚦 <b>{actor}</b> изменил приоритет\n📌 {task_title}\n{old} → {new}"

        if activity.action == "due_date_changed":
            old = activity.old_value or "не задан"
            new = activity.new_value or "не задан"
            return f"📅 <b>{actor}</b> изменил дедлайн\n📌 {task_title}\n{old} → {new}"

        if activity.action == "title_changed":
            return f"✏️ <b>{actor}</b> переименовал задачу\n📌 {task_title}"

        if activity.action == "completed":
            return f"✅ <b>{actor}</b> завершил задачу\n📌 {task_title}"

        if activity.action == "description_changed":
            return f"📝 <b>{actor}</b> обновил описание\n📌 {task_title}"

        return f"📝 <b>{actor}</b> обновил задачу\n📌 {task_title}"
