import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.core.security import verify_access_token
from app.models.auth import Organization, User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Необходима авторизация",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    user_id = verify_access_token(credentials.credentials)
    if not user_id:
        raise credentials_exception

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Аккаунт неактивен")
    return current_user


def require_role(*roles: UserRole):
    """Фабрика dependency для проверки роли."""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется: {[r.value for r in roles]}",
            )
        return current_user

    return role_checker


# ─── Tenant session ───────────────────────────────────────────────────────────
async def get_tenant_session(
    current_user: Annotated[User, Depends(get_current_user)],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Возвращает AsyncSession с search_path, установленным на schema текущей организации.
    Загружает schema_name из public.organizations по organization_id пользователя.
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не привязан к организации",
        )

    async with AsyncSessionLocal() as meta_db:
        result = await meta_db.execute(
            select(Organization).where(Organization.id == current_user.organization_id)
        )
        org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Организация не найдена")

    async with AsyncSessionLocal() as session:
        await session.execute(
            text(f'SET LOCAL search_path TO "{org.schema_name}", public')
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Удобные алиасы
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role(UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN))]
ManagerUser = Annotated[
    User,
    Depends(require_role(UserRole.MANAGER, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN)),
]
TenantDB = Annotated[AsyncSession, Depends(get_tenant_session)]
