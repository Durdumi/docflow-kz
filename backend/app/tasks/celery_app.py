from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "docflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.document_tasks",
        "app.tasks.report_tasks",
        "app.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Almaty",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "telegram-polling": {
            "task": "notification_tasks.run_telegram_polling",
            "schedule": 6.0,
        },
        "daily-task-reminders": {
            "task": "notification_tasks.daily_task_reminders",
            "schedule": crontab(hour=9, minute=0),
        },
    },
)
