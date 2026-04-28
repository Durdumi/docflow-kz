import json
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import cast, or_, select, text, desc
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_db
from app.core.config import settings
from app.models.auth import Organization, User
from app.models.tasks import Task
from app.models.documents import Document, DocumentStatus
from app.models.reports import Report, ReportStatus, ReportType, ReportFormat
from app.models.imports import DataImport
from app.services.telegram_state import get_state, set_state, update_data, get_data, clear_state

router = APIRouter(prefix="/telegram", tags=["Telegram"])


# ─── Helpers ──────────────────────────────────────────────────
async def send_tg(chat_id: str, text: str, keyboard: dict | None = None):
    import httpx
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json=payload, timeout=10,
        )
    return resp


async def answer_cb(callback_id: str, text: str = ""):
    import httpx
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
            json={"callback_query_id": callback_id, "text": text},
            timeout=10,
        )


async def edit_tg_reply_markup(chat_id: str, message_id: int, keyboard: dict):
    import httpx
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageReplyMarkup",
            json={"chat_id": chat_id, "message_id": message_id, "reply_markup": json.dumps(keyboard)},
            timeout=10,
        )


def _build_assignees_keyboard(users_data: list[dict], selected_ids: list[str]) -> dict:
    buttons = []
    for u in users_data:
        prefix = "✅ " if u["id"] in selected_ids else ""
        buttons.append([{
            "text": f"{prefix}{u['name']}",
            "callback_data": f"task_create_toggle_{u['id']}",
        }])
    n = len(selected_ids)
    if n > 0:
        buttons.append([{"text": f"✔ Подтвердить ({n} выбр.)", "callback_data": "task_create_confirm_assignees"}])
    else:
        buttons.append([{"text": "⏭ Пропустить", "callback_data": "task_create_skip_assignee"}])
    buttons.append([{"text": "✖ Отмена", "callback_data": "task_create_cancel"}])
    return {"inline_keyboard": buttons}


async def get_user(chat_id: str, db: AsyncSession) -> User | None:
    result = await db.execute(
        select(User).where(User.telegram_chat_id == chat_id, User.is_active == True)
    )
    return result.scalar_one_or_none()


async def get_org(user: User, db: AsyncSession) -> Organization | None:
    if not user.organization_id:
        return None
    result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    return result.scalar_one_or_none()


async def set_tenant_schema(org: Organization, db: AsyncSession):
    await db.execute(text(f'SET search_path TO "{org.schema_name}", public'))


# ─── Main Menu ────────────────────────────────────────────────
async def send_main_menu(chat_id: str, user: User):
    keyboard = {"inline_keyboard": [
        [
            {"text": "📋 Задачи", "callback_data": "menu_tasks"},
            {"text": "📄 Документы", "callback_data": "menu_docs"},
        ],
        [
            {"text": "📊 Отчёты", "callback_data": "menu_reports"},
            {"text": "📥 Импорты", "callback_data": "menu_imports"},
        ],
        [
            {"text": "👤 Мой профиль", "callback_data": "menu_profile"},
        ],
    ]}
    await send_tg(
        chat_id,
        f"🏠 <b>DocFlow KZ</b>\n\n"
        f"Привет, <b>{user.first_name} {user.last_name}</b>!\n"
        f"Выберите раздел:",
        keyboard,
    )


# ─── TASKS MENU ───────────────────────────────────────────────
async def handle_tasks_menu(chat_id: str, user: User, db: AsyncSession):
    keyboard = {"inline_keyboard": [
        [{"text": "📋 Мои активные задачи", "callback_data": "tasks_my"}],
        [{"text": "✅ Завершить задачу", "callback_data": "tasks_done_list"}],
        [{"text": "⚡ Взять в работу", "callback_data": "tasks_start_list"}],
        [{"text": "➕ Создать задачу", "callback_data": "tasks_create"}],
        [{"text": "« Главное меню", "callback_data": "main_menu"}],
    ]}
    await send_tg(chat_id, "📋 <b>Задачи</b>\nВыберите действие:", keyboard)


async def handle_tasks_my(chat_id: str, user: User, db: AsyncSession):
    org = await get_org(user, db)
    if not org:
        await send_tg(chat_id, "❌ Организация не найдена")
        return
    await set_tenant_schema(org, db)

    result = await db.execute(
        select(Task).where(
            Task.organization_id == user.organization_id,
            Task.status.notin_(["done"]),
            or_(
                Task.assignee_id == user.id,
                Task.assignee_ids.op("@>")(cast([str(user.id)], JSONB)),
            ),
        ).order_by(Task.created_at.desc()).limit(10)
    )
    tasks = result.scalars().all()

    if not tasks:
        await send_tg(chat_id, "✅ У вас нет активных задач!", {
            "inline_keyboard": [[{"text": "« Назад", "callback_data": "menu_tasks"}]]
        })
        return

    STATUS_EMOJI = {"todo": "📋", "in_progress": "⚡", "review": "👀", "done": "✅"}
    PRIORITY_EMOJI = {"low": "↓", "medium": "→", "high": "↑", "urgent": "🔥"}

    lines = []
    buttons = []
    for task in tasks:
        s = STATUS_EMOJI.get(task.status, "📋")
        p = PRIORITY_EMOJI.get(task.priority, "→")
        due = f" | до {task.due_date.strftime('%d.%m')}" if task.due_date else ""
        lines.append(f"{s} {p} <b>{task.title[:40]}</b>{due}")
        buttons.append([{"text": f"{s} {task.title[:35]}", "callback_data": f"task_view_{task.id}"}])

    buttons.append([{"text": "« Назад", "callback_data": "menu_tasks"}])
    msg = f"📋 <b>Ваши задачи ({len(tasks)}):</b>\n\n" + "\n".join(lines)
    await send_tg(chat_id, msg, {"inline_keyboard": buttons})


async def handle_task_view(chat_id: str, task_id: str, user: User, db: AsyncSession):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    try:
        uid = uuid.UUID(task_id)
    except ValueError:
        return

    result = await db.execute(select(Task).where(Task.id == uid))
    task = result.scalar_one_or_none()
    if not task:
        await send_tg(chat_id, "❌ Задача не найдена")
        return

    STATUS_LABELS = {
        "todo": "📋 Надо сделать",
        "in_progress": "⚡ В работе",
        "review": "👀 На проверке",
        "done": "✅ Готово",
    }
    PRIORITY_LABELS = {
        "low": "↓ Низкий", "medium": "→ Средний",
        "high": "↑ Высокий", "urgent": "🔥 Срочно",
    }

    due_text = ""
    if task.due_date:
        from datetime import datetime, UTC
        overdue = task.due_date.replace(tzinfo=None) < datetime.utcnow()
        due_text = f"\n📅 Дедлайн: {task.due_date.strftime('%d.%m.%Y')}"
        if overdue and task.status != "done":
            due_text += " ⚠️"

    desc_text = f"\n📝 {task.description[:100]}" if task.description else ""

    msg = (
        f"📌 <b>{task.title}</b>{desc_text}\n\n"
        f"📊 {STATUS_LABELS.get(task.status, task.status)}\n"
        f"🚦 {PRIORITY_LABELS.get(task.priority, task.priority)}"
        f"{due_text}"
    )

    buttons = []
    status_buttons = []
    if task.status != "in_progress":
        status_buttons.append({"text": "⚡ В работу", "callback_data": f"task_setstatus_{task.id}_in_progress"})
    if task.status != "review":
        status_buttons.append({"text": "👀 На проверку", "callback_data": f"task_setstatus_{task.id}_review"})
    if task.status != "done":
        status_buttons.append({"text": "✅ Готово", "callback_data": f"task_setstatus_{task.id}_done"})
    if task.status != "todo":
        status_buttons.append({"text": "↩️ Вернуть", "callback_data": f"task_setstatus_{task.id}_todo"})

    for i in range(0, len(status_buttons), 2):
        buttons.append(status_buttons[i:i+2])

    buttons.append([{"text": "👥 Управление ответственными", "callback_data": f"task_manage_assignees_{task.id}"}])
    buttons.append([{"text": "« К задачам", "callback_data": "tasks_my"}])
    buttons.append([{"text": "🏠 Меню", "callback_data": "main_menu"}])

    await send_tg(chat_id, msg, {"inline_keyboard": buttons})


async def handle_task_setstatus(chat_id: str, task_id: str, new_status: str, user: User, db: AsyncSession, callback_id: str):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    try:
        uid = uuid.UUID(task_id)
    except ValueError:
        await answer_cb(callback_id, "❌ Ошибка")
        return

    result = await db.execute(select(Task).where(Task.id == uid))
    task = result.scalar_one_or_none()
    if not task:
        await answer_cb(callback_id, "❌ Задача не найдена")
        return

    old_status = task.status
    task.status = new_status
    if new_status == "done":
        from datetime import datetime, UTC
        task.completed_at = datetime.now(UTC)
    else:
        task.completed_at = None

    from app.models.activity import TaskActivity
    activity = TaskActivity(
        task_id=task.id,
        organization_id=task.organization_id,
        actor_id=user.id,
        actor_name=f"{user.last_name} {user.first_name}",
        action="completed" if new_status == "done" else "status_changed",
        field_name="status",
        old_value=old_status,
        new_value=new_status,
    )
    db.add(activity)
    await db.commit()

    STATUS_LABELS = {
        "todo": "📋 Надо сделать",
        "in_progress": "⚡ В работе",
        "review": "👀 На проверке",
        "done": "✅ Готово",
    }

    await answer_cb(callback_id, f"✅ {STATUS_LABELS.get(new_status, new_status)}")

    if task.created_by_id != user.id:
        await db.execute(text("SET search_path TO public"))
        r = await db.execute(select(User).where(User.id == task.created_by_id))
        creator = r.scalar_one_or_none()
        if creator and creator.telegram_chat_id:
            from app.services.telegram_service import send_message
            await send_message(
                creator.telegram_chat_id,
                f"🔄 <b>{user.first_name} {user.last_name}</b> изменил статус задачи\n"
                f"📌 {task.title}\n"
                f"{STATUS_LABELS.get(old_status, old_status)} → {STATUS_LABELS.get(new_status, new_status)}"
            )

    await send_tg(
        chat_id,
        f"✅ Статус задачи обновлён:\n<b>{task.title}</b>\n→ {STATUS_LABELS.get(new_status, new_status)}",
        {"inline_keyboard": [
            [{"text": "📋 К задачам", "callback_data": "tasks_my"}],
            [{"text": "🏠 Меню", "callback_data": "main_menu"}],
        ]}
    )


# ─── DOCUMENTS MENU ───────────────────────────────────────────
async def handle_docs_menu(chat_id: str, user: User, db: AsyncSession):
    keyboard = {"inline_keyboard": [
        [{"text": "📄 Список документов", "callback_data": "docs_list"}],
        [{"text": "📋 Черновики", "callback_data": "docs_drafts"}],
        [{"text": "✅ Активные", "callback_data": "docs_active"}],
        [{"text": "« Главное меню", "callback_data": "main_menu"}],
    ]}
    await send_tg(chat_id, "📄 <b>Документы</b>\nВыберите действие:", keyboard)


async def handle_docs_list(chat_id: str, user: User, db: AsyncSession, status_filter: str | None = None):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    query = select(Document).where(
        Document.organization_id == user.organization_id,
    ).order_by(desc(Document.created_at)).limit(10)

    if status_filter:
        query = query.where(Document.status == status_filter)

    result = await db.execute(query)
    docs = result.scalars().all()

    if not docs:
        label = {"draft": "черновиков", "active": "активных документов"}.get(status_filter or "", "документов")
        await send_tg(chat_id, f"📭 Нет {label}", {
            "inline_keyboard": [[{"text": "« Назад", "callback_data": "menu_docs"}]]
        })
        return

    STATUS_EMOJI = {"draft": "📝", "active": "✅", "archived": "📦"}
    lines = []
    buttons = []
    for doc in docs:
        s = STATUS_EMOJI.get(doc.status, "📄")
        lines.append(f"{s} <b>{doc.title[:45]}</b>")
        buttons.append([{"text": f"{s} {doc.title[:40]}", "callback_data": f"doc_view_{doc.id}"}])

    buttons.append([{"text": "« Назад", "callback_data": "menu_docs"}])
    msg = f"📄 <b>Документы ({len(docs)}):</b>\n\n" + "\n".join(lines)
    await send_tg(chat_id, msg, {"inline_keyboard": buttons})


async def handle_doc_view(chat_id: str, doc_id: str, user: User, db: AsyncSession):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    try:
        uid = uuid.UUID(doc_id)
    except ValueError:
        return

    result = await db.execute(select(Document).where(Document.id == uid))
    doc = result.scalar_one_or_none()
    if not doc:
        await send_tg(chat_id, "❌ Документ не найден")
        return

    STATUS_LABELS = {"draft": "📝 Черновик", "active": "✅ Активный", "archived": "📦 Архив"}
    created = doc.created_at.strftime("%d.%m.%Y %H:%M")

    msg = (
        f"📄 <b>{doc.title}</b>\n\n"
        f"📊 Статус: {STATUS_LABELS.get(doc.status, doc.status)}\n"
        f"📅 Создан: {created}\n"
        f"🔢 Полей: {len(doc.data) if doc.data else 0}"
    )

    buttons = []
    if doc.status == "draft":
        buttons.append([{"text": "✅ Активировать", "callback_data": f"doc_setstatus_{doc.id}_active"}])
    if doc.status == "active":
        buttons.append([{"text": "📦 В архив", "callback_data": f"doc_setstatus_{doc.id}_archived"}])
    if doc.status == "archived":
        buttons.append([{"text": "✅ Активировать", "callback_data": f"doc_setstatus_{doc.id}_active"}])

    buttons.append([{"text": "« К документам", "callback_data": "docs_list"}])
    buttons.append([{"text": "🏠 Меню", "callback_data": "main_menu"}])

    await send_tg(chat_id, msg, {"inline_keyboard": buttons})


async def handle_doc_setstatus(chat_id: str, doc_id: str, new_status: str, user: User, db: AsyncSession, callback_id: str):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    try:
        uid = uuid.UUID(doc_id)
    except ValueError:
        await answer_cb(callback_id, "❌ Ошибка")
        return

    result = await db.execute(select(Document).where(Document.id == uid))
    doc = result.scalar_one_or_none()
    if not doc:
        await answer_cb(callback_id, "❌ Документ не найден")
        return

    doc.status = new_status
    await db.commit()

    STATUS_LABELS = {"draft": "📝 Черновик", "active": "✅ Активный", "archived": "📦 Архив"}
    await answer_cb(callback_id, f"✅ {STATUS_LABELS.get(new_status, new_status)}")
    await send_tg(
        chat_id,
        f"✅ Статус документа обновлён:\n<b>{doc.title}</b>\n→ {STATUS_LABELS.get(new_status, new_status)}",
        {"inline_keyboard": [
            [{"text": "📄 К документам", "callback_data": "docs_list"}],
            [{"text": "🏠 Меню", "callback_data": "main_menu"}],
        ]}
    )


# ─── REPORTS MENU ─────────────────────────────────────────────
async def handle_reports_menu(chat_id: str, user: User, db: AsyncSession):
    keyboard = {"inline_keyboard": [
        [{"text": "📊 Список отчётов", "callback_data": "reports_list"}],
        [{"text": "➕ Создать отчёт", "callback_data": "reports_create_menu"}],
        [{"text": "⏳ Статус генерации", "callback_data": "reports_pending"}],
        [{"text": "« Главное меню", "callback_data": "main_menu"}],
    ]}
    await send_tg(chat_id, "📊 <b>Отчёты</b>\nВыберите действие:", keyboard)


async def handle_reports_list(chat_id: str, user: User, db: AsyncSession):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    result = await db.execute(
        select(Report).where(
            Report.organization_id == user.organization_id,
        ).order_by(desc(Report.created_at)).limit(8)
    )
    reports = result.scalars().all()

    if not reports:
        await send_tg(chat_id, "📭 Отчётов пока нет", {
            "inline_keyboard": [[{"text": "« Назад", "callback_data": "menu_reports"}]]
        })
        return

    STATUS_EMOJI = {"pending": "⏳", "generating": "🔄", "ready": "✅", "failed": "❌"}
    TYPE_LABELS = {
        "weekly": "Еженедельный", "monthly": "Ежемесячный",
        "quarterly": "Квартальный", "annual": "Годовой", "custom": "Произвольный",
    }

    lines = []
    buttons = []
    for r in reports:
        s = STATUS_EMOJI.get(r.status, "📊")
        t = TYPE_LABELS.get(r.type, r.type)
        lines.append(f"{s} <b>{r.title[:35]}</b> — {t}")
        buttons.append([{"text": f"{s} {r.title[:38]}", "callback_data": f"report_view_{r.id}"}])

    buttons.append([{"text": "« Назад", "callback_data": "menu_reports"}])
    msg = f"📊 <b>Отчёты ({len(reports)}):</b>\n\n" + "\n".join(lines)
    await send_tg(chat_id, msg, {"inline_keyboard": buttons})


async def handle_report_view(chat_id: str, report_id: str, user: User, db: AsyncSession):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    try:
        uid = uuid.UUID(report_id)
    except ValueError:
        return

    result = await db.execute(select(Report).where(Report.id == uid))
    report = result.scalar_one_or_none()
    if not report:
        await send_tg(chat_id, "❌ Отчёт не найден")
        return

    STATUS_LABELS = {
        "pending": "⏳ Ожидает", "generating": "🔄 Генерируется",
        "ready": "✅ Готов", "failed": "❌ Ошибка",
    }
    TYPE_LABELS = {
        "weekly": "Еженедельный", "monthly": "Ежемесячный",
        "quarterly": "Квартальный", "annual": "Годовой", "custom": "Произвольный",
    }

    size_text = ""
    if report.file_size:
        size_text = f"\n📦 Размер: {report.file_size // 1024} KB"

    period_text = ""
    if report.period_from and report.period_to:
        period_text = f"\n📅 Период: {report.period_from.strftime('%d.%m.%Y')} — {report.period_to.strftime('%d.%m.%Y')}"

    msg = (
        f"📊 <b>{report.title}</b>\n\n"
        f"📋 Тип: {TYPE_LABELS.get(report.type, report.type)}\n"
        f"📊 Формат: {report.format.upper()}\n"
        f"🔄 Статус: {STATUS_LABELS.get(report.status, report.status)}"
        f"{period_text}{size_text}"
    )

    buttons = []
    if report.status == "ready":
        buttons.append([{"text": "📥 Скачать (открыть в браузере)", "callback_data": f"report_download_info_{report.id}"}])
    if report.status == "failed":
        buttons.append([{"text": "🔄 Повторить генерацию", "callback_data": f"report_regenerate_{report.id}"}])

    buttons.append([{"text": "« К отчётам", "callback_data": "reports_list"}])
    buttons.append([{"text": "🏠 Меню", "callback_data": "main_menu"}])

    await send_tg(chat_id, msg, {"inline_keyboard": buttons})


async def handle_reports_create_menu(chat_id: str, user: User, db: AsyncSession):
    keyboard = {"inline_keyboard": [
        [
            {"text": "📅 Еженедельный", "callback_data": "report_create_weekly_pdf"},
            {"text": "📆 Ежемесячный", "callback_data": "report_create_monthly_pdf"},
        ],
        [
            {"text": "📊 Квартальный", "callback_data": "report_create_quarterly_pdf"},
            {"text": "📈 Годовой", "callback_data": "report_create_annual_pdf"},
        ],
        [
            {"text": "📄 PDF формат", "callback_data": "report_format_pdf"},
            {"text": "📊 Excel формат", "callback_data": "report_format_excel"},
        ],
        [{"text": "« Назад", "callback_data": "menu_reports"}],
    ]}
    await send_tg(chat_id, "➕ <b>Создать отчёт</b>\nВыберите тип и формат:", keyboard)


async def handle_report_create(chat_id: str, report_type: str, fmt: str, user: User, db: AsyncSession, callback_id: str):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    from datetime import datetime, UTC, timedelta
    now = datetime.now(UTC)

    TYPE_LABELS = {
        "weekly": "Еженедельный", "monthly": "Ежемесячный",
        "quarterly": "Квартальный", "annual": "Годовой",
    }

    if report_type == "weekly":
        period_from = now - timedelta(days=7)
        period_to = now
    elif report_type == "monthly":
        period_from = now.replace(day=1)
        period_to = now
    elif report_type == "quarterly":
        period_from = now - timedelta(days=90)
        period_to = now
    else:
        period_from = now.replace(month=1, day=1)
        period_to = now

    title = f"{TYPE_LABELS.get(report_type, report_type)} отчёт {now.strftime('%d.%m.%Y')}"

    report = Report(
        title=title,
        type=report_type,
        format=fmt,
        status=ReportStatus.PENDING,
        period_from=period_from,
        period_to=period_to,
        parameters={},
        created_by_id=user.id,
        organization_id=user.organization_id,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    await db.commit()

    from app.tasks.report_tasks import generate_report_task
    generate_report_task.delay(str(report.id), org.schema_name)

    await answer_cb(callback_id, "✅ Отчёт поставлен в очередь")
    await send_tg(
        chat_id,
        f"🔄 <b>Отчёт создан и поставлен в очередь!</b>\n\n"
        f"📊 {title}\n"
        f"📋 Формат: {fmt.upper()}\n\n"
        f"Когда отчёт будет готов — вы получите уведомление.",
        {"inline_keyboard": [
            [{"text": "📊 К отчётам", "callback_data": "reports_list"}],
            [{"text": "🏠 Меню", "callback_data": "main_menu"}],
        ]}
    )


# ─── IMPORTS MENU ─────────────────────────────────────────────
async def handle_imports_menu(chat_id: str, user: User, db: AsyncSession):
    keyboard = {"inline_keyboard": [
        [{"text": "📥 Список импортов", "callback_data": "imports_list"}],
        [{"text": "ℹ️ Как загрузить файл", "callback_data": "imports_howto"}],
        [{"text": "« Главное меню", "callback_data": "main_menu"}],
    ]}
    await send_tg(chat_id, "📥 <b>Импорт данных</b>\nВыберите действие:", keyboard)


async def handle_imports_list(chat_id: str, user: User, db: AsyncSession):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    result = await db.execute(
        select(DataImport).where(
            DataImport.organization_id == user.organization_id,
        ).order_by(desc(DataImport.created_at)).limit(8)
    )
    imports = result.scalars().all()

    if not imports:
        await send_tg(chat_id, "📭 Нет загруженных файлов\n\nЗагрузите файл через веб-интерфейс DocFlow KZ", {
            "inline_keyboard": [[{"text": "« Назад", "callback_data": "menu_imports"}]]
        })
        return

    SOURCE_EMOJI = {"excel": "📊", "csv": "📋", "json": "🔧"}
    CATEGORY_LABELS = {
        "salary": "Зарплата", "finance": "Финансы", "hr": "Кадры",
        "sales": "Продажи", "stock": "Склад", "other": "Прочее",
    }

    lines = []
    for imp in imports:
        s = SOURCE_EMOJI.get(imp.source_type, "📄")
        cat = CATEGORY_LABELS.get(imp.category or "", imp.category or "—")
        lines.append(f"{s} <b>{imp.name[:35]}</b> — {cat} | {imp.row_count} строк")

    msg = f"📥 <b>Импорты ({len(imports)}):</b>\n\n" + "\n".join(lines)
    await send_tg(chat_id, msg, {
        "inline_keyboard": [[{"text": "« Назад", "callback_data": "menu_imports"}]]
    })


# ─── PROFILE ──────────────────────────────────────────────────
async def handle_profile(chat_id: str, user: User, db: AsyncSession):
    org = await get_org(user, db)
    org_name = org.name if org else "—"

    ROLE_LABELS = {
        "super_admin": "Супер-админ",
        "org_admin": "Администратор",
        "manager": "Менеджер",
        "user": "Пользователь",
    }

    msg = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"👤 {user.last_name} {user.first_name}\n"
        f"📧 {user.email}\n"
        f"🏢 {org_name}\n"
        f"🎭 {ROLE_LABELS.get(user.role, user.role)}\n"
        f"📱 Telegram: подключён ✅"
    )

    await send_tg(chat_id, msg, {
        "inline_keyboard": [[{"text": "🏠 Главное меню", "callback_data": "main_menu"}]]
    })


# ─── MANAGE ASSIGNEES ─────────────────────────────────────────
async def handle_manage_assignees(chat_id: str, task_id: str, user: User, db: AsyncSession, callback_id: str):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    try:
        uid = uuid.UUID(task_id)
    except ValueError:
        return

    result = await db.execute(select(Task).where(Task.id == uid))
    task = result.scalar_one_or_none()
    if not task:
        await send_tg(chat_id, "❌ Задача не найдена")
        return

    await db.execute(text("SET search_path TO public"))
    users_result = await db.execute(
        select(User).where(
            User.organization_id == user.organization_id,
            User.is_active == True,
        ).limit(15)
    )
    org_users = users_result.scalars().all()

    current_ids = [str(x) for x in (task.assignee_ids or [])]

    buttons = []
    assignee_names = []
    for u in org_users:
        is_assigned = str(u.id) in current_ids
        if is_assigned:
            assignee_names.append(f"{u.last_name} {u.first_name}")
        action = "remove" if is_assigned else "add"
        prefix = "✅ " if is_assigned else "➕ "
        buttons.append([{
            "text": f"{prefix}{u.last_name} {u.first_name}",
            "callback_data": f"task_assignee_{action}_{task.id}_{u.id}",
        }])

    buttons.append([{"text": "« Назад к задаче", "callback_data": f"task_view_{task.id}"}])

    current_text = "\n".join(f"• {n}" for n in assignee_names) if assignee_names else "никто"
    await send_tg(
        chat_id,
        f"👥 <b>Ответственные:</b>\n📌 {task.title}\n\n"
        f"Текущие:\n{current_text}\n\n"
        f"Нажмите чтобы добавить / убрать:",
        {"inline_keyboard": buttons},
    )


async def handle_toggle_assignee(
    chat_id: str, action: str, task_id: str, target_user_id: str,
    user: User, db: AsyncSession, callback_id: str,
):
    org = await get_org(user, db)
    if not org:
        return
    await set_tenant_schema(org, db)

    try:
        task_uid = uuid.UUID(task_id)
        target_uid = uuid.UUID(target_user_id)
    except ValueError:
        await answer_cb(callback_id, "❌ Ошибка")
        return

    result = await db.execute(select(Task).where(Task.id == task_uid))
    task = result.scalar_one_or_none()
    if not task:
        await answer_cb(callback_id, "❌ Задача не найдена")
        return

    current_ids = [str(x) for x in (task.assignee_ids or [])]

    if action == "add" and str(target_uid) not in current_ids:
        current_ids.append(str(target_uid))
        await db.execute(text("SET search_path TO public"))
        r = await db.execute(select(User).where(User.id == target_uid))
        target_user = r.scalar_one_or_none()
        if target_user and target_user.telegram_chat_id and target_user.id != user.id:
            from app.services.telegram_service import send_message
            await send_message(
                target_user.telegram_chat_id,
                f"👤 Вас добавили как ответственного!\n\n"
                f"📌 {task.title}\n"
                f"Добавил: {user.last_name} {user.first_name}",
            )
        await db.execute(text(f'SET search_path TO "{org.schema_name}", public'))
    elif action == "remove" and str(target_uid) in current_ids:
        current_ids.remove(str(target_uid))

    task.assignee_ids = current_ids
    task.assignee_id = uuid.UUID(current_ids[0]) if current_ids else None
    await db.commit()
    await answer_cb(callback_id, "✅ Обновлено")

    await handle_manage_assignees(chat_id, task_id, user, db, callback_id)


# ─── TASK CREATE DIALOG ───────────────────────────────────────
async def handle_task_create_start(chat_id: str, user: User):
    set_state(chat_id, "waiting_title")
    await send_tg(
        chat_id,
        "➕ <b>Создание задачи — Шаг 1 из 4</b>\n\n"
        "Введите <b>название задачи</b>:",
        {"inline_keyboard": [[{"text": "✖ Отмена", "callback_data": "task_create_cancel"}]]},
    )


async def handle_task_create_dialog(chat_id: str, text_input: str, user: User, db: AsyncSession):
    state = get_state(chat_id)

    if state == "waiting_title":
        title = text_input.strip()
        if len(title) < 2:
            await send_tg(chat_id, "❌ Название слишком короткое. Введите ещё раз:")
            return
        update_data(chat_id, title=title)
        await ask_task_priority(chat_id, user)

    elif state == "waiting_due_date":
        raw = text_input.strip().lower()
        if raw in ("нет", "skip", "-", "пропустить"):
            update_data(chat_id, due_date=None)
        else:
            from datetime import datetime
            parsed = None
            for fmt in ("%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    parsed = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    continue
            if not parsed:
                await send_tg(
                    chat_id,
                    "❌ Не удалось распознать дату. Введите в формате <b>дд.мм.гггг</b> или нажмите «Пропустить»:",
                    {"inline_keyboard": [
                        [{"text": "⏭ Пропустить", "callback_data": "task_create_skip_due"}],
                        [{"text": "✖ Отмена", "callback_data": "task_create_cancel"}],
                    ]},
                )
                return
            update_data(chat_id, due_date=parsed.isoformat())
        await ask_task_assignees(chat_id, user, db)

    else:
        await send_tg(
            chat_id,
            "🏠 Используйте кнопки меню.",
            {"inline_keyboard": [[{"text": "🏠 Меню", "callback_data": "main_menu"}]]},
        )


async def ask_task_priority(chat_id: str, user: User):
    set_state(chat_id, "waiting_priority")
    await send_tg(
        chat_id,
        "➕ <b>Создание задачи — Шаг 2 из 4</b>\n\nВыберите <b>приоритет</b>:",
        {"inline_keyboard": [
            [
                {"text": "↓ Низкий", "callback_data": "task_create_priority_low"},
                {"text": "→ Средний", "callback_data": "task_create_priority_medium"},
            ],
            [
                {"text": "↑ Высокий", "callback_data": "task_create_priority_high"},
                {"text": "🔥 Срочно", "callback_data": "task_create_priority_urgent"},
            ],
            [{"text": "✖ Отмена", "callback_data": "task_create_cancel"}],
        ]},
    )


async def ask_task_due_date(chat_id: str, user: User):
    set_state(chat_id, "waiting_due_date")
    await send_tg(
        chat_id,
        "➕ <b>Создание задачи — Шаг 3 из 4</b>\n\n"
        "Введите <b>дедлайн</b> в формате дд.мм.гггг\nили нажмите «Пропустить»:",
        {"inline_keyboard": [
            [{"text": "⏭ Пропустить", "callback_data": "task_create_skip_due"}],
            [{"text": "✖ Отмена", "callback_data": "task_create_cancel"}],
        ]},
    )


async def ask_task_assignees(chat_id: str, user: User, db: AsyncSession):
    set_state(chat_id, "waiting_assignees")
    update_data(chat_id, selected_assignees=[])

    result = await db.execute(
        select(User).where(
            User.organization_id == user.organization_id,
            User.is_active == True,
        ).limit(10)
    )
    users = result.scalars().all()

    users_data = []
    for u in users:
        name = f"{u.last_name} {u.first_name}"
        if u.id == user.id:
            name += " (я)"
        users_data.append({"id": str(u.id), "name": name})
    update_data(chat_id, assignees_list=users_data)

    keyboard = _build_assignees_keyboard(users_data, [])
    resp = await send_tg(
        chat_id,
        "➕ <b>Создание задачи — Шаг 4 из 4</b>\n\nВыберите <b>исполнителей</b> (можно несколько):",
        keyboard,
    )
    try:
        msg_id = resp.json()["result"]["message_id"]
        update_data(chat_id, assignees_msg_id=msg_id)
    except Exception:
        pass


async def finalize_task_create(chat_id: str, user: User, db: AsyncSession):
    data = get_data(chat_id)
    clear_state(chat_id)

    org = await get_org(user, db)
    if not org:
        await send_tg(chat_id, "❌ Организация не найдена")
        return
    await set_tenant_schema(org, db)

    from datetime import datetime
    from app.models.boards import Board as BoardModel

    due_date = None
    if data.get("due_date"):
        try:
            due_date = datetime.fromisoformat(data["due_date"])
        except Exception:
            pass

    board_result = await db.execute(
        select(BoardModel).where(
            BoardModel.organization_id == user.organization_id,
            BoardModel.is_archived == False,
        ).order_by(BoardModel.created_at).limit(1)
    )
    default_board = board_result.scalar_one_or_none()

    selected: list[str] = data.get("selected_assignees") or []
    first_assignee_id = uuid.UUID(selected[0]) if selected else None

    task = Task(
        title=data.get("title", "Без названия"),
        priority=data.get("priority", "medium"),
        due_date=due_date,
        assignee_id=first_assignee_id,
        assignee_ids=selected,
        board_id=default_board.id if default_board else None,
        created_by_id=user.id,
        organization_id=user.organization_id,
        status="todo",
        checklist=[],
        attachments=[],
        comments=[],
        label_ids=[],
        watch_user_ids=[],
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    PRIORITY_EMOJI = {"low": "↓", "medium": "→", "high": "↑", "urgent": "🔥"}
    due_text = f"\n📅 Дедлайн: {task.due_date.strftime('%d.%m.%Y')}" if task.due_date else ""
    p_emoji = PRIORITY_EMOJI.get(str(task.priority), "→")

    users_data: list[dict] = data.get("assignees_list") or []
    name_map = {u["id"]: u["name"] for u in users_data}
    assignees_text = ""
    if selected:
        names = [name_map.get(uid, uid) for uid in selected]
        assignees_text = f"\n👤 Исполнители: {', '.join(names)}"

    await send_tg(
        chat_id,
        f"✅ <b>Задача создана!</b>\n\n"
        f"📌 <b>{task.title}</b>\n"
        f"{p_emoji} Приоритет: {task.priority}{due_text}{assignees_text}",
        {"inline_keyboard": [
            [{"text": "📋 Мои задачи", "callback_data": "tasks_my"}],
            [{"text": "🏠 Главное меню", "callback_data": "main_menu"}],
        ]},
    )


# ─── WEBHOOK HANDLER ──────────────────────────────────────────
@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        data = await request.json()
    except Exception:
        return {"ok": True}

    # ─── Callback Query (кнопки) ──────────────────────────────
    if "callback_query" in data:
        cb = data["callback_query"]
        chat_id = str(cb["message"]["chat"]["id"])
        cb_id = cb["id"]
        cb_data = cb.get("data", "")

        user = await get_user(chat_id, db)
        if not user:
            await answer_cb(cb_id, "❌ Не авторизован. Напишите /start")
            return {"ok": True}

        await answer_cb(cb_id)

        # ─── Routing ──────────────────────────────────────────
        if cb_data == "main_menu":
            await send_main_menu(chat_id, user)

        # Tasks
        elif cb_data == "menu_tasks":
            await handle_tasks_menu(chat_id, user, db)
        elif cb_data == "tasks_my":
            await handle_tasks_my(chat_id, user, db)
        elif cb_data.startswith("task_view_"):
            task_id = cb_data.replace("task_view_", "")
            await handle_task_view(chat_id, task_id, user, db)
        elif cb_data.startswith("task_setstatus_"):
            # task_setstatus_{uuid}_{status}
            without = cb_data.replace("task_setstatus_", "")
            parts = without.rsplit("_", 1)
            if len(parts) == 2:
                await handle_task_setstatus(chat_id, parts[0], parts[1], user, db, cb_id)
        elif cb_data == "tasks_done_list":
            await handle_tasks_my(chat_id, user, db)
        elif cb_data == "tasks_start_list":
            await handle_tasks_my(chat_id, user, db)
        elif cb_data == "tasks_create":
            await handle_task_create_start(chat_id, user)

        # Task create dialog callbacks
        elif cb_data.startswith("task_create_priority_"):
            priority = cb_data.replace("task_create_priority_", "")
            update_data(chat_id, priority=priority)
            await ask_task_due_date(chat_id, user)
        elif cb_data == "task_create_skip_due":
            update_data(chat_id, due_date=None)
            await ask_task_assignees(chat_id, user, db)
        elif cb_data.startswith("task_create_toggle_"):
            uid_str = cb_data.replace("task_create_toggle_", "")
            d = get_data(chat_id)
            selected: list[str] = list(d.get("selected_assignees") or [])
            if uid_str in selected:
                selected.remove(uid_str)
            else:
                selected.append(uid_str)
            update_data(chat_id, selected_assignees=selected)
            users_data = d.get("assignees_list") or []
            msg_id = d.get("assignees_msg_id")
            if msg_id:
                await edit_tg_reply_markup(chat_id, msg_id, _build_assignees_keyboard(users_data, selected))
        elif cb_data == "task_create_confirm_assignees":
            await finalize_task_create(chat_id, user, db)
        elif cb_data == "task_create_skip_assignee":
            update_data(chat_id, selected_assignees=[])
            await finalize_task_create(chat_id, user, db)
        elif cb_data == "task_create_cancel":
            clear_state(chat_id)
            await handle_tasks_menu(chat_id, user, db)

        # Manage assignees
        elif cb_data.startswith("task_manage_assignees_"):
            task_id = cb_data.replace("task_manage_assignees_", "")
            await handle_manage_assignees(chat_id, task_id, user, db, cb_id)
        elif cb_data.startswith("task_assignee_"):
            # task_assignee_{add|remove}_{task_uuid}_{user_uuid}
            without = cb_data.replace("task_assignee_", "")
            parts = without.split("_", 1)
            if len(parts) == 2:
                action = parts[0]
                rest = parts[1]
                if len(rest) >= 73:  # 36 + "_" + 36
                    await handle_toggle_assignee(chat_id, action, rest[:36], rest[37:], user, db, cb_id)

        # Documents
        elif cb_data == "menu_docs":
            await handle_docs_menu(chat_id, user, db)
        elif cb_data == "docs_list":
            await handle_docs_list(chat_id, user, db)
        elif cb_data == "docs_drafts":
            await handle_docs_list(chat_id, user, db, "draft")
        elif cb_data == "docs_active":
            await handle_docs_list(chat_id, user, db, "active")
        elif cb_data.startswith("doc_view_"):
            doc_id = cb_data.replace("doc_view_", "")
            await handle_doc_view(chat_id, doc_id, user, db)
        elif cb_data.startswith("doc_setstatus_"):
            without = cb_data.replace("doc_setstatus_", "")
            parts = without.rsplit("_", 1)
            if len(parts) == 2:
                await handle_doc_setstatus(chat_id, parts[0], parts[1], user, db, cb_id)

        # Reports
        elif cb_data == "menu_reports":
            await handle_reports_menu(chat_id, user, db)
        elif cb_data == "reports_list":
            await handle_reports_list(chat_id, user, db)
        elif cb_data.startswith("report_view_"):
            report_id = cb_data.replace("report_view_", "")
            await handle_report_view(chat_id, report_id, user, db)
        elif cb_data == "reports_create_menu":
            await handle_reports_create_menu(chat_id, user, db)
        elif cb_data.startswith("report_create_"):
            # report_create_{type}_{format}
            without = cb_data.replace("report_create_", "")
            parts = without.rsplit("_", 1)
            if len(parts) == 2:
                await handle_report_create(chat_id, parts[0], parts[1], user, db, cb_id)
        elif cb_data.startswith("report_download_info_"):
            await send_tg(chat_id,
                "📥 Для скачивания отчёта откройте:\n"
                "http://localhost:3000/reports\n\n"
                "Найдите отчёт и нажмите кнопку 'Скачать'.\n"
                "В следующей версии скачивание будет доступно прямо в боте.",
                {"inline_keyboard": [[{"text": "« К отчётам", "callback_data": "reports_list"}]]}
            )

        # Imports
        elif cb_data == "menu_imports":
            await handle_imports_menu(chat_id, user, db)
        elif cb_data == "imports_list":
            await handle_imports_list(chat_id, user, db)
        elif cb_data == "imports_howto":
            await send_tg(chat_id,
                "📥 <b>Как загрузить файл:</b>\n\n"
                "1. Откройте DocFlow KZ в браузере\n"
                "2. Перейдите в раздел 'Импорт данных'\n"
                "3. Нажмите 'Загрузить файл'\n"
                "4. Выберите Excel (.xlsx), CSV или JSON файл\n"
                "5. Укажите название и категорию\n\n"
                "Поддерживаемые форматы: Excel, CSV, JSON\n"
                "Максимальный размер: 10 MB",
                {"inline_keyboard": [[{"text": "« Назад", "callback_data": "menu_imports"}]]}
            )

        # Profile
        elif cb_data == "menu_profile":
            await handle_profile(chat_id, user, db)

        return {"ok": True}

    # ─── Message (команды) ────────────────────────────────────
    if "message" not in data:
        return {"ok": True}

    msg = data["message"]
    chat_id = str(msg.get("chat", {}).get("id", ""))
    text_msg = msg.get("text", "").strip()

    if not chat_id:
        return {"ok": True}

    user = await get_user(chat_id, db)

    if text_msg.startswith("/start"):
        if user:
            await send_main_menu(chat_id, user)
        else:
            await send_tg(
                chat_id,
                f"👋 Добро пожаловать в <b>DocFlow KZ</b>!\n\n"
                f"🔑 Ваш Chat ID:\n<code>{chat_id}</code>\n\n"
                f"Скопируйте этот ID и вставьте в:\n"
                f"⚙️ Настройки → Профиль → Telegram Chat ID\n\n"
                f"После этого вы получите доступ ко всем функциям бота.",
            )
        return {"ok": True}

    if not user:
        await send_tg(
            chat_id,
            f"❌ Вы не авторизованы.\n\n"
            f"Ваш Chat ID: <code>{chat_id}</code>\n"
            f"Вставьте его в Настройки → Профиль → Telegram Chat ID"
        )
        return {"ok": True}

    # Диалог создания задачи — перехват до команд
    active_state = get_state(chat_id)
    if active_state in ("waiting_title", "waiting_due_date"):
        await handle_task_create_dialog(chat_id, text_msg, user, db)
        return {"ok": True}

    # Команды
    if text_msg.startswith("/tasks"):
        await handle_tasks_my(chat_id, user, db)
    elif text_msg.startswith("/docs"):
        await handle_docs_list(chat_id, user, db)
    elif text_msg.startswith("/reports"):
        await handle_reports_list(chat_id, user, db)
    elif text_msg.startswith("/imports"):
        await handle_imports_list(chat_id, user, db)
    elif text_msg.startswith("/profile"):
        await handle_profile(chat_id, user, db)
    elif text_msg.startswith("/help"):
        await send_tg(chat_id,
            "📚 <b>Команды DocFlow KZ бота:</b>\n\n"
            "/start — Главное меню\n"
            "/tasks — Мои задачи\n"
            "/docs — Документы\n"
            "/reports — Отчёты\n"
            "/imports — Импорты\n"
            "/profile — Мой профиль\n"
            "/help — Помощь"
        )
    else:
        await send_main_menu(chat_id, user)

    return {"ok": True}


@router.post("/set-webhook")
async def set_webhook(request: Request):
    import httpx
    body = await request.json()
    webhook_url = body.get("webhook_url")
    if not webhook_url:
        raise HTTPException(status_code=400, detail="webhook_url required")
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


@router.get("/webhook-info")
async def webhook_info():
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getWebhookInfo"
        )
    return response.json()
