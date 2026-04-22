"""
Telegram webhook + команды бота.
Пользователь пишет /start боту → получает свой chat_id →
вводит его в Settings → уведомления включены.
"""
import httpx
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.auth import User
from app.services.telegram_service import send_telegram_message

router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Принимает обновления от Telegram."""
    data = await request.json()
    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "")

    if not chat_id:
        return {"ok": True}

    if text.startswith("/start"):
        reply = (
            f"👋 <b>Добро пожаловать в DocFlow KZ!</b>\n\n"
            f"Ваш Telegram ID:\n"
            f"<code>{chat_id}</code>\n\n"
            f"Скопируйте этот ID и вставьте его в:\n"
            f"⚙️ Настройки → Профиль → Telegram ID\n\n"
            f"После этого вы будете получать уведомления о готовых отчётах "
            f"и важных событиях."
        )
        await send_telegram_message(chat_id, reply)

    elif text.startswith("/help"):
        reply = (
            f"📋 <b>Доступные команды:</b>\n\n"
            f"/start — получить ваш Telegram ID\n"
            f"/help — список команд\n"
            f"/status — статус подключения"
        )
        await send_telegram_message(chat_id, reply)

    elif text.startswith("/status"):
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.telegram_chat_id == chat_id)
            )
            user = result.scalar_one_or_none()
        if user:
            reply = f"✅ Подключён как <b>{user.first_name} {user.last_name}</b>"
        else:
            reply = (
                "❌ Аккаунт не привязан. "
                "Добавьте Telegram ID в настройках DocFlow KZ."
            )
        await send_telegram_message(chat_id, reply)

    return {"ok": True}


@router.post("/set-webhook")
async def set_webhook(webhook_url: str):
    """Установить webhook URL для бота (вызывается один раз при деплое)."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN не настроен")

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={"url": webhook_url})
    return response.json()


@router.get("/test/{chat_id}")
async def test_notification(chat_id: str):
    """Тестовое уведомление (только для разработки)."""
    success = await send_telegram_message(
        chat_id,
        "🎉 <b>DocFlow KZ</b>\n\nТестовое уведомление работает! ✅",
    )
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Не удалось отправить сообщение. Проверьте TELEGRAM_BOT_TOKEN и chat_id.",
        )
    return {"ok": True, "message": "Отправлено"}
