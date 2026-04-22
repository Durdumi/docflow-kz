from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ─── Engine ───────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ─── Base Models ──────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Public schema (organizations, users, ...)."""


class TenantBase(DeclarativeBase):
    """Tenant schema (documents, templates, ...) — schema-per-org."""


# ─── Dependency ───────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Multitenant: Schema per Organization ─────────────────────────────────────
async def get_tenant_db(schema_name: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Возвращает сессию с активным search_path для конкретного тенанта.
    Использование: async with get_tenant_db("org_medtech") as db: ...
    """
    async with AsyncSessionLocal() as session:
        try:
            # Устанавливаем schema для этой сессии
            await session.execute(
                text(f'SET search_path TO "{schema_name}", public')
            )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # Сбрасываем search_path
            await session.execute(text("SET search_path TO public"))
            await session.close()


async def create_tenant_schema(schema_name: str) -> None:
    """Создаёт schema для новой организации."""
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))


async def apply_tenant_tables(schema_name: str) -> None:
    """Создаёт таблицы tenant schema (document_templates, documents, reports).
    Вызывается при регистрации новой организации.
    """
    import app.models.documents  # noqa: F401
    import app.models.reports    # noqa: F401
    import app.models.imports    # noqa: F401

    async with engine.begin() as conn:
        # Только tenant schema — без public в fallback, иначе create_all находит
        # одноимённые таблицы из public и пропускает создание в tenant schema.
        await conn.execute(text(f'SET search_path TO "{schema_name}"'))
        await conn.run_sync(TenantBase.metadata.create_all)
        await conn.execute(text("SET search_path TO public"))


async def drop_tenant_schema(schema_name: str) -> None:
    """Удаляет schema организации (только для тестов/удаления)."""
    async with engine.begin() as conn:
        await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))


@asynccontextmanager
async def tenant_session(schema_name: str):
    """Context manager для использования вне FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(
                text(f'SET search_path TO "{schema_name}", public')
            )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
