from fastapi import APIRouter

from app.api.v1.endpoints import auth, reports
from app.api.v1.endpoints.documents import documents_router, templates_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(templates_router)
api_router.include_router(documents_router)
api_router.include_router(reports.router)

# Будем добавлять по мере разработки:
# api_router.include_router(organizations.router)
# api_router.include_router(users.router)
# api_router.include_router(imports.router)
