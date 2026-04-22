import json
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.core.config import settings
from app.models.auth import Organization, User
from app.models.tasks import Task

router = APIRouter(prefix="/telegram", tags=["Telegram"])


async def _get_user_by_chat_id(chat_id: str, db: AsyncSession) -> User | None:
    result = await db.execute(
        select(User).where(User.telegram_chat_id == chat_id, User.is_active == True)
    )
    return result.scalar_one_or_none()


async def _get_user_tasks(user: User, db: AsyncSession, status_filter: list[str] | None = None) -> list:
    if not user.organization_id:
        return []
    org_result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = org_result.scalar_one_or_none()
    if not org:
        return []
    await db.execute(text(f'SET search_path TO "{org.schema_name}", public'))
    query = select(Task).where(
        Task.assignee_id == user.id,
        Task.organization_id == user.organization_id,
    )
    if status_filter:
        query = query.where(Task.status.in_(status_filter))
    else:
        query = query.where(Task.status.notin_(["done"]))
    result = await db.execute(query.order_by(Task.created_at.desc()).limit(10))
    return list(result.scalars().all())


async def _send(chat_id: str, text: str, reply_markup: dict | None = None):
    import httpx
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json=payload,
        )


async def _answer_callback(callback_query_id: str, text: str = ""):
    import httpx
    if not settings.TELEGRAM_BOT_TOKEN:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text},
        )


async def _send_main_menu(chat_id: str, user: User):
    await _send(
        chat_id,
        f"👋 Привет, <b>{user.first_name}</b>!\n\nЧто хотите сделать?",
        reply_markup={"inline_keyboard": [
            [{"text": "📋 Мои задачи", "callback_data": "tasks_list"}],
            [{"text": "✅ Отметить выполненной", "callback_data": "tasks_done_list"}],
        ]},
    )


STATUS_LABELS = {
    "todo": "📋 Надо сделать",
    "in_progress": "⚡ В работе",
    "review": "👀 На проверке",
    "done": "✅ Готово",
}

PRIORITY_EMOJI = {"low": "↓", "medium": "→", "high": "↑", "urgent": "🔥"}


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    # ─── Callback Query (inline кнопки) ───────────────────────
    if "callback_query" in data:
        cb = data["callback_query"]
        chat_id = str(cb["message"]["chat"]["id"])
        cb_id = cb["id"]
        cb_data = cb.get("data", "")

        user = await _get_user_by_chat_id(chat_id, db)
        if not user:
            await _answer_callback(cb_id, "❌ Не авторизован")
            return {"ok": True}

        if cb_data == "main_menu":
            await _answer_callback(cb_id)
            await _send_main_menu(chat_id, user)

        elif cb_data == "tasks_list":
            await _answer_callback(cb_id)
            tasks = await _get_user_tasks(user, db)
            if not tasks:
                await _send(chat_id, "✅ У вас нет активных задач!", reply_markup={"inline_keyboard": [
                    [{"text": "🏠 Главное меню", "callback_data": "main_menu"}]
                ]})
                return {"ok": True}
            buttons = [
                [{"text": f"{PRIORITY_EMOJI.get(t.priority, '→')} {t.title[:45]}", "callback_data": f"task_view_{t.id}"}]
                for t in tasks
            ]
            buttons.append([{"text": "🏠 Главное меню", "callback_data": "main_menu"}])
            await _send(chat_id, f"📋 <b>Активные задачи ({len(tasks)}):</b>", reply_markup={"inline_keyboard": buttons})

        elif cb_data == "tasks_done_list":
            await _answer_callback(cb_id)
            tasks = await _get_user_tasks(user, db, status_filter=["todo", "in_progress", "review"])
            if not tasks:
                await _send(chat_id, "✅ Нет задач для завершения!", reply_markup={"inline_keyboard": [
                    [{"text": "🏠 Главное меню", "callback_data": "main_menu"}]
                ]})
                return {"ok": True}
            buttons = [
                [{"text": f"✅ {t.title[:45]}", "callback_data": f"task_status_{t.id}_done"}]
                for t in tasks
            ]
            buttons.append([{"text": "🏠 Главное меню", "callback_data": "main_menu"}])
            await _send(chat_id, "Выберите задачу для завершения:", reply_markup={"inline_keyboard": buttons})

        elif cb_data.startswith("task_view_"):
            await _answer_callback(cb_id)
            task_id_str = cb_data.replace("task_view_", "")
            import uuid as _uuid
            try:
                uid = _uuid.UUID(task_id_str)
            except ValueError:
                return {"ok": True}

            org_result = await db.execute(select(Organization).where(Organization.id == user.organization_id))
            org = org_result.scalar_one_or_none()
            if org:
                await db.execute(text(f'SET search_path TO "{org.schema_name}", public'))

            task_result = await db.execute(select(Task).where(Task.id == uid))
            task = task_result.scalar_one_or_none()
            if not task:
                await _send(chat_id, "❌ Задача не найдена")
                return {"ok": True}

            due_text = ""
            if task.due_date:
                from datetime import datetime
                overdue = task.due_date.replace(tzinfo=None) < datetime.utcnow()
                due_text = f"\n📅 Дедлайн: {task.due_date.strftime('%d.%m.%Y')}"
                if overdue and task.status != "done":
                    due_text += " ⚠️ ПРОСРОЧЕНО"

            desc_text = f"\n📝 {task.description[:100]}" if task.description else ""
            msg = (
                f"📌 <b>{task.title}</b>{desc_text}\n"
                f"📊 Статус: {STATUS_LABELS.get(task.status, task.status)}\n"
                f"🚦 Приоритет: {PRIORITY_EMOJI.get(task.priority, '→')} {task.priority}"
                f"{due_text}"
            )

            btns = []
            for st, label in STATUS_LABELS.items():
                if st != task.status:
                    btns.append({"text": label, "callback_data": f"task_status_{task.id}_{st}"})
            keyboard = [btns[i:i+2] for i in range(0, len(btns), 2)]
            keyboard.append([{"text": "« К списку", "callback_data": "tasks_list"}])
            await _send(chat_id, msg, reply_markup={"inline_keyboard": keyboard})

        elif cb_data.startswith("task_status_"):
            without_prefix = cb_data.replace("task_status_", "")
            # UUID содержит дефисы — последний сегмент после последнего _ это статус
            # in_progress содержит _ поэтому ищем по известным статусам
            new_status = None
            task_id_str = None
            for st in ["in_progress", "todo", "review", "done"]:
                if without_prefix.endswith(f"_{st}"):
                    new_status = st
                    task_id_str = without_prefix[: -(len(st) + 1)]
                    break

            if not new_status or not task_id_str:
                await _answer_callback(cb_id, "❌ Ошибка")
                return {"ok": True}

            import uuid as _uuid
            try:
                uid = _uuid.UUID(task_id_str)
            except ValueError:
                await _answer_callback(cb_id, "❌ Ошибка ID")
                return {"ok": True}

            org_result = await db.execute(select(Organization).where(Organization.id == user.organization_id))
            org = org_result.scalar_one_or_none()
            if org:
                await db.execute(text(f'SET search_path TO "{org.schema_name}", public'))

            task_result = await db.execute(select(Task).where(Task.id == uid))
            task = task_result.scalar_one_or_none()
            if not task:
                await _answer_callback(cb_id, "❌ Задача не найдена")
                return {"ok": True}

            task.status = new_status
            if new_status == "done":
                from datetime import datetime, UTC
                task.completed_at = datetime.now(UTC)
            else:
                task.completed_at = None
            await db.commit()

            await _answer_callback(cb_id, f"✅ {STATUS_LABELS.get(new_status, new_status)}")
            await _send(
                chat_id,
                f"✅ <b>{task.title}</b>\nСтатус: {STATUS_LABELS.get(new_status, new_status)}",
                reply_markup={"inline_keyboard": [
                    [{"text": "📋 К списку задач", "callback_data": "tasks_list"}],
                    [{"text": "🏠 Главное меню", "callback_data": "main_menu"}],
                ]},
            )

        return {"ok": True}

    # ─── Обычные сообщения ─────────────────────────────────────
    if "message" not in data:
        return {"ok": True}

    msg = data["message"]
    chat_id = str(msg.get("chat", {}).get("id", ""))
    text_msg = (msg.get("text") or "").strip()
    if not chat_id:
        return {"ok": True}

    user = await _get_user_by_chat_id(chat_id, db)

    if text_msg.startswith("/start"):
        if user:
            await _send_main_menu(chat_id, user)
        else:
            await _send(
                chat_id,
                f"👋 <b>Добро пожаловать в DocFlow KZ!</b>\n\n"
                f"Ваш Chat ID:\n<code>{chat_id}</code>\n\n"
                f"Скопируйте этот ID и вставьте в:\n"
                f"⚙️ Настройки → Профиль → Telegram Chat ID\n\n"
                f"После этого вы сможете управлять задачами прямо из Telegram."
            )
        return {"ok": True}

    if not user:
        await _send(
            chat_id,
            f"❌ Аккаунт не привязан.\n\nВаш Chat ID: <code>{chat_id}</code>\n"
            f"Вставьте его в Настройки → Профиль → Telegram Chat ID"
        )
        return {"ok": True}

    if text_msg.startswith("/tasks"):
        tasks = await _get_user_tasks(user, db)
        if not tasks:
            await _send(chat_id, "✅ Нет активных задач!")
            return {"ok": True}
        buttons = [
            [{"text": f"{PRIORITY_EMOJI.get(t.priority, '→')} {t.title[:50]}", "callback_data": f"task_view_{t.id}"}]
            for t in tasks
        ]
        await _send(chat_id, f"📋 <b>Активные задачи ({len(tasks)}):</b>", reply_markup={"inline_keyboard": buttons})
        return {"ok": True}

    if text_msg.startswith("/done"):
        tasks = await _get_user_tasks(user, db, status_filter=["todo", "in_progress", "review"])
        if not tasks:
            await _send(chat_id, "✅ Нет задач для завершения!")
            return {"ok": True}
        buttons = [
            [{"text": f"✅ {t.title[:50]}", "callback_data": f"task_status_{t.id}_done"}]
            for t in tasks
        ]
        await _send(chat_id, "Выберите задачу для завершения:", reply_markup={"inline_keyboard": buttons})
        return {"ok": True}

    if text_msg.startswith("/status"):
        await _send(
            chat_id,
            f"✅ Подключён как <b>{user.first_name} {user.last_name}</b>\n({user.email})",
            reply_markup={"inline_keyboard": [[{"text": "📋 Мои задачи", "callback_data": "tasks_list"}]]}
        )
        return {"ok": True}

    # Любое другое сообщение — показываем меню
    await _send_main_menu(chat_id, user)
    return {"ok": True}


@router.post("/set-webhook")
async def set_webhook(request: Request):
    import httpx
    body = await request.json()
    webhook_url = body.get("webhook_url")
    if not webhook_url:
        raise HTTPException(status_code=400, detail="webhook_url required")
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN не настроен")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook",
            json={"url": webhook_url},
        )
    return response.json()


@router.get("/test/{chat_id}")
async def test_notification(chat_id: str):
    from app.services.telegram_service import send_message
    result = await send_message(chat_id, "🔔 Тест уведомления DocFlow KZ работает!")
    return {"sent": result}
