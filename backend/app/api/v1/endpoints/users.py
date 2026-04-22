import secrets
import string
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AdminUser, CurrentUser, get_db
from app.core.security import get_password_hash
from app.models.auth import User, UserRole
from app.schemas.auth import InviteUserRequest, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/profile", response_model=UserRead)
async def get_profile(current_user: CurrentUser):
    return UserRead.model_validate(current_user)


@router.patch("/me/profile", response_model=UserRead)
async def update_profile(
    data: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return UserRead.model_validate(current_user)


@router.get("", response_model=list[UserRead])
async def list_users(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Нет организации")
    result = await db.execute(
        select(User)
        .where(
            User.organization_id == current_user.organization_id,
            User.is_active == True,  # noqa: E712
        )
        .order_by(User.created_at)
    )
    return [UserRead.model_validate(u) for u in result.scalars().all()]


@router.post("/invite", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def invite_user(
    data: InviteUserRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.execute(select(User).where(User.email == data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    alphabet = string.ascii_letters + string.digits
    temp_password = "".join(secrets.choice(alphabet) for _ in range(12))

    user = User(
        email=data.email.lower(),
        hashed_password=get_password_hash(temp_password),
        first_name=data.first_name,
        last_name=data.last_name,
        organization_id=current_user.organization_id,
        role=data.role,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    await db.commit()
    return UserRead.model_validate(user)


@router.patch("/{user_id}/role", response_model=UserRead)
async def change_user_role(
    user_id: uuid.UUID,
    role: UserRole,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя изменить свою роль")
    user.role = role
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.patch("/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя деактивировать себя")
    user.is_active = False
    await db.commit()
