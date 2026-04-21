from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser
from app.core.database import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация организации",
)
async def register(
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Создаёт новую организацию и первого администратора.
    Автоматически генерирует отдельную PostgreSQL schema для тенанта.
    """
    service = AuthService(db)
    try:
        return await service.register(data)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход в систему",
)
async def login(
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AuthService(db)
    try:
        return await service.login(data.email, data.password)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновить токены",
)
async def refresh_tokens(
    data: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AuthService(db)
    try:
        return await service.refresh_tokens(data.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
)
async def logout(
    data: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = AuthService(db)
    await service.logout(data.refresh_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Текущий пользователь",
)
async def get_me(current_user: CurrentUser):
    return current_user
