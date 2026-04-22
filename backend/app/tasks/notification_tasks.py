"""
Telegram bot polling task.
Celery beat запускает каждые 3 секунды.
Redis lock предотвращает одновременный запуск нескольких копий.
"""
from app.tasks.celery_app import celery_app


@celery_app.task(name="notification_tasks.run_telegram_polling", bind=True, max_retries=0)
def run_telegram_polling(self):
    import asyncio
    import httpx
    from app.core.config import settings
    from app.core.database import AsyncSessionLocal
    from app.services.telegram_service import send_telegram_message
    from sqlalchemy import select
    from app.models.auth import User

    if not settings.TELEGRAM_BOT_TOKEN:
        return

    token = settings.TELEGRAM_BOT_TOKEN
    base_url = f"https://api.telegram.org/bot{token}"
    offset_key = "tg:poll:offset"
    lock_key = "tg:poll:lock"

    async def _handle_message(message: dict):
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = (message.get("text") or "").strip()
        if not chat_id:
            return

        if text.startswith("/start"):
            await send_telegram_message(
                chat_id,
                f"👋 <b>Добро пожаловать в DocFlow KZ!</b>\n\n"
                f"Ваш Telegram ID:\n<code>{chat_id}</code>\n\n"
                f"Скопируйте этот ID и вставьте в:\n"
                f"⚙️ Настройки → Профиль → Telegram ID\n\n"
                f"После этого вы будете получать уведомления о готовых отчётах.",
            )

        elif text.startswith("/help"):
            await send_telegram_message(
                chat_id,
                "📋 <b>Команды:</b>\n\n"
                "/start — получить ваш Telegram ID\n"
                "/status — статус привязки аккаунта\n"
                "/help — эта справка",
            )

        elif text.startswith("/status"):
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(User).where(User.telegram_chat_id == chat_id)
                )
                user = result.scalar_one_or_none()
            if user:
                reply = (
                    f"✅ Подключён как "
                    f"<b>{user.first_name} {user.last_name}</b> ({user.email})"
                )
            else:
                reply = (
                    "❌ Аккаунт не привязан.\n"
                    "Добавьте ваш Telegram ID в Настройки → Профиль."
                )
            await send_telegram_message(chat_id, reply)

    async def _run():
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)

        # Distributed lock — если предыдущий poll ещё идёт, пропустить
        lock = await r.set(lock_key, "1", nx=True, ex=10)
        if not lock:
            await r.aclose()
            return

        try:
            offset = int(await r.get(offset_key) or 0)

            async with httpx.AsyncClient(timeout=8) as client:
                try:
                    resp = await client.get(
                        f"{base_url}/getUpdates",
                        params={"offset": offset, "timeout": 5, "limit": 20},
                    )
                    data = resp.json()
                except Exception:
                    return

            if not data.get("ok"):
                return

            updates = data.get("result", [])
            for update in updates:
                update_id = update.get("update_id", 0)
                message = update.get("message") or update.get("edited_message")
                if message:
                    await _handle_message(message)
                offset = update_id + 1

            if updates:
                await r.set(offset_key, offset)

        finally:
            await r.delete(lock_key)
            await r.aclose()

    asyncio.run(_run())


@celery_app.task(name="notification_tasks.daily_task_reminders")
def daily_task_reminders():
    """Запускается каждый день в 9:00 — напоминает об активных тасках."""
    import asyncio
    asyncio.run(_send_daily_reminders())


async def _send_daily_reminders():
    import uuid as uuid_module
    from datetime import datetime, UTC
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    from app.core.config import settings
    from app.models.auth import Organization, User
    from app.models.tasks import Task
    from app.services.telegram_service import send_message

    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        orgs_result = await db.execute(select(Organization))
        orgs = orgs_result.scalars().all()

        for org in orgs:
            schema = org.schema_name
            try:
                await db.execute(text(f'SET search_path TO "{schema}", public'))

                tasks_result = await db.execute(
                    select(Task).where(
                        Task.organization_id == org.id,
                        Task.status.in_(["todo", "in_progress", "review"]),
                        Task.assignee_id.isnot(None),
                    )
                )
                tasks = tasks_result.scalars().all()

                tasks_by_user: dict = {}
                for task in tasks:
                    uid = str(task.assignee_id)
                    tasks_by_user.setdefault(uid, []).append(task)

                await db.execute(text("SET search_path TO public"))

                for user_id, user_tasks in tasks_by_user.items():
                    user_result = await db.execute(
                        select(User).where(User.id == uuid_module.UUID(user_id))
                    )
                    user = user_result.scalar_one_or_none()
                    if not user or not user.telegram_chat_id:
                        continue

                    task_lines = []
                    for t in user_tasks[:5]:
                        overdue = t.due_date and t.due_date.replace(tzinfo=None) < datetime.utcnow()
                        line = f"{'🔴' if overdue else '📋'} {t.title}"
                        if t.due_date:
                            line += f" (до {t.due_date.strftime('%d.%m')})"
                        task_lines.append(line)

                    if len(user_tasks) > 5:
                        task_lines.append(f"...и ещё {len(user_tasks) - 5} задач")

                    msg = (
                        f"☀️ Доброе утро, {user.first_name}!\n\n"
                        f"У вас <b>{len(user_tasks)}</b> активных задач:\n"
                        + "\n".join(task_lines)
                        + "\n\nОткройте DocFlow KZ для управления задачами."
                    )
                    await send_message(user.telegram_chat_id, msg)

            except Exception as e:
                print(f"Error processing org {org.slug}: {e}")
                continue

    await engine.dispose()
