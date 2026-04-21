import uuid
from datetime import UTC, datetime, timedelta

from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import apply_tenant_tables, create_tenant_schema
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.auth import Organization, OrgPlan, OrgStatus, RefreshToken, User, UserRole
from app.schemas.auth import RegisterRequest, TokenResponse, UserRead


class AuthError(Exception):
    """Базовое исключение для auth-ошибок."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Registration ─────────────────────────────────────────────────────────
    async def register(self, data: RegisterRequest) -> TokenResponse:
        """
        Регистрирует новую организацию и первого admin-пользователя.
        Создаёт отдельную PostgreSQL schema для тенанта.
        """
        # Проверяем уникальность email
        existing_user = await self._get_user_by_email(data.email)
        if existing_user:
            raise AuthError("Пользователь с таким email уже существует")

        # Генерируем slug и schema_name для организации
        base_slug = slugify(data.organization_name, separator="_", lowercase=True)
        slug = await self._ensure_unique_slug(base_slug)
        schema_name = f"org_{slug}"

        # Создаём организацию
        organization = Organization(
            name=data.organization_name,
            slug=slug,
            schema_name=schema_name,
            contact_email=data.organization_email,
            contact_phone=data.organization_phone,
            city=data.city,
            bin_number=data.bin_number,
            plan=OrgPlan.TRIAL,
            status=OrgStatus.TRIAL,
        )
        self.db.add(organization)
        await self.db.flush()  # Получаем ID организации

        # Создаём PostgreSQL schema и таблицы для этого тенанта
        await create_tenant_schema(schema_name)
        await apply_tenant_tables(schema_name)

        # Создаём пользователя-админа
        user = User(
            email=data.email.lower().strip(),
            hashed_password=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            middle_name=data.middle_name,
            organization_id=organization.id,
            role=UserRole.ORG_ADMIN,
            is_active=True,
            is_verified=False,  # Нужна верификация email
        )
        self.db.add(user)
        await self.db.flush()

        # Генерируем токены
        tokens = await self._create_tokens(user)
        await self.db.commit()

        await self.db.refresh(user)
        return TokenResponse(
            access_token=tokens["access"],
            refresh_token=tokens["refresh"],
            user=UserRead.model_validate(user),
        )

    # ─── Login ────────────────────────────────────────────────────────────────
    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self._get_user_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise AuthError("Неверный email или пароль", status_code=401)

        if not user.is_active:
            raise AuthError("Аккаунт заблокирован", status_code=403)

        # Обновляем last_login
        user.last_login_at = datetime.now(UTC)

        tokens = await self._create_tokens(user)
        await self.db.commit()
        await self.db.refresh(user)

        return TokenResponse(
            access_token=tokens["access"],
            refresh_token=tokens["refresh"],
            user=UserRead.model_validate(user),
        )

    # ─── Refresh Token ────────────────────────────────────────────────────────
    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record or token_record.is_expired:
            raise AuthError("Refresh token недействителен или истёк", status_code=401)

        # Ротация токена (инвалидируем старый)
        token_record.is_revoked = True

        user_result = await self.db.execute(
            select(User).where(User.id == token_record.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthError("Пользователь не найден", status_code=401)

        tokens = await self._create_tokens(user)
        await self.db.commit()
        await self.db.refresh(user)

        return TokenResponse(
            access_token=tokens["access"],
            refresh_token=tokens["refresh"],
            user=UserRead.model_validate(user),
        )

    # ─── Logout ───────────────────────────────────────────────────────────────
    async def logout(self, refresh_token: str) -> None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token_record = result.scalar_one_or_none()
        if token_record:
            token_record.is_revoked = True
            await self.db.commit()

    # ─── Private Helpers ──────────────────────────────────────────────────────
    async def _get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(func.lower(User.email) == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def _create_tokens(self, user: User) -> dict[str, str]:
        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))

        # Сохраняем refresh token в БД
        refresh_record = RefreshToken(
            user_id=user.id,
            token=refresh,
            expires_at=datetime.now(UTC) + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            ),
        )
        self.db.add(refresh_record)

        return {"access": access, "refresh": refresh}

    async def _ensure_unique_slug(self, base_slug: str) -> str:
        slug = base_slug
        counter = 1
        while True:
            result = await self.db.execute(
                select(Organization).where(Organization.slug == slug)
            )
            if not result.scalar_one_or_none():
                return slug
            slug = f"{base_slug}_{counter}"
            counter += 1
