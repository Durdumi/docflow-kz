from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ─── App ──────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_NAME: str = "DocFlow KZ"
    APP_SECRET_KEY: str = "change_me"
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"

    # ─── Database ─────────────────────────────────────────────
    DATABASE_URL: str
    POSTGRES_USER: str = "docflow"
    POSTGRES_PASSWORD: str = "docflow_secret"
    POSTGRES_DB: str = "docflow"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    # ─── Redis / Celery ───────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # ─── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change_me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ─── MinIO ────────────────────────────────────────────────
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin_secret"
    MINIO_BUCKET_DOCUMENTS: str = "documents"
    MINIO_BUCKET_REPORTS: str = "reports"
    MINIO_SECURE: bool = False

    # ─── Email ────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@docflow.kz"
    EMAILS_FROM_NAME: str = "DocFlow KZ"

    # ─── Telegram ─────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = ""

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
