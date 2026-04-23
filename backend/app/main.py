import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Действия при старте и остановке приложения."""
    # Startup: создаём таблицы public schema (если не существуют)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    await engine.dispose()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Платформа автоматизации документооборота и отчётности",
        docs_url="/api/docs" if settings.APP_DEBUG else None,
        redoc_url="/api/redoc" if settings.APP_DEBUG else None,
        openapi_url="/api/openapi.json" if settings.APP_DEBUG else None,
        lifespan=lifespan,
    )

    # ─── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            # В production добавить домен
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["docflow.kz", "*.docflow.kz"],
        )

    # ─── Routers ──────────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ─── Health check ─────────────────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
        }

    # ─── Frontend SPA (должно быть ПОСЛЕДНИМ — catch-all) ────────────────────
    _dist = "/app/frontend_dist"
    if os.path.exists(_dist):
        _assets = f"{_dist}/assets"
        if os.path.exists(_assets):
            app.mount("/assets", StaticFiles(directory=_assets), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            index = f"{_dist}/index.html"
            if os.path.exists(index):
                return FileResponse(index)
            return {"error": "Frontend not built"}

    return app


app = create_application()
