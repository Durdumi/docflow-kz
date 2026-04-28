from fastapi import APIRouter

from app.api.v1.endpoints import auth, boards, imports, organizations, reports, telegram, users
from app.api.v1.endpoints.documents import documents_router, templates_router
from app.api.v1.endpoints.tasks import router as tasks_router, calendar_router
from app.api.v1.endpoints.board_config import router as board_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(templates_router)
api_router.include_router(documents_router)
api_router.include_router(reports.router)
api_router.include_router(imports.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)
api_router.include_router(telegram.router)
api_router.include_router(tasks_router)
api_router.include_router(calendar_router)
api_router.include_router(board_router)
api_router.include_router(boards.router)
