import httpx
from app.core.config import settings

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


async def send_telegram_message(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        return False

    url = TELEGRAM_API.format(token=settings.TELEGRAM_BOT_TOKEN, method="sendMessage")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            })
            return response.status_code == 200
    except Exception:
        return False


async def send_report_ready(chat_id: str, report_title: str, report_id: str) -> bool:
    text = (
        f"✅ <b>Отчёт готов!</b>\n\n"
        f"📄 <b>{report_title}</b>\n\n"
        f"Войдите в DocFlow KZ чтобы скачать отчёт.\n"
        f"🆔 ID: <code>{report_id}</code>"
    )
    return await send_telegram_message(chat_id, text)


async def send_report_failed(chat_id: str, report_title: str, error: str) -> bool:
    text = (
        f"❌ <b>Ошибка генерации отчёта</b>\n\n"
        f"📄 <b>{report_title}</b>\n\n"
        f"Причина: {error[:200]}"
    )
    return await send_telegram_message(chat_id, text)


async def send_document_created(chat_id: str, doc_title: str, created_by: str) -> bool:
    text = (
        f"📁 <b>Новый документ создан</b>\n\n"
        f"📝 <b>{doc_title}</b>\n"
        f"👤 Создал: {created_by}"
    )
    return await send_telegram_message(chat_id, text)


async def send_user_invited(
    chat_id: str,
    org_name: str,
    temp_password: str,
    login_url: str = "http://localhost:3000",
) -> bool:
    text = (
        f"👋 <b>Вас добавили в {org_name}</b>\n\n"
        f"Войдите в DocFlow KZ:\n"
        f"🔗 {login_url}\n\n"
        f"🔑 Временный пароль: <code>{temp_password}</code>\n\n"
        f"Смените пароль после первого входа."
    )
    return await send_telegram_message(chat_id, text)


async def send_message(chat_id: str, text: str) -> bool:
    print(f"[Telegram] BOT_TOKEN exists: {bool(settings.TELEGRAM_BOT_TOKEN)}, chat_id: {chat_id}")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            )
            print(f"[Telegram] Response: {response.status_code} {response.text[:200]}")
            return response.status_code == 200
    except Exception as e:
        print(f"[Telegram] Error: {e}")
        return False


async def send_task_assigned(
    chat_id: str,
    task_title: str,
    due_date=None,
    priority: str = "medium",
) -> bool:
    print(f"[Telegram] send_task_assigned -> chat_id={chat_id}, title={task_title}")
    priority_emoji = {"low": "↓", "medium": "→", "high": "↑", "urgent": "🔥"}.get(priority, "→")
    due_text = ""
    if due_date:
        from datetime import datetime
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        due_text = f"\n📅 Дедлайн: {due_date.strftime('%d.%m.%Y')}"
    text = (
        f"📌 <b>Вам назначена новая задача!</b>\n\n"
        f"📋 {task_title}\n"
        f"{priority_emoji} Приоритет: {priority}{due_text}\n\n"
        f"Откройте DocFlow KZ для просмотра деталей."
    )
    result = await send_message(chat_id, text)
    print(f"[Telegram] send_task_assigned result: {result}")
    return result


async def send_deadline_reminder(chat_id: str, doc_title: str, days_left: int) -> bool:
    emoji = "🔴" if days_left <= 1 else "🟡" if days_left <= 3 else "🟢"
    text = (
        f"{emoji} <b>Напоминание о дедлайне</b>\n\n"
        f"📝 {doc_title}\n"
        f"⏰ Осталось дней: <b>{days_left}</b>"
    )
    return await send_telegram_message(chat_id, text)
