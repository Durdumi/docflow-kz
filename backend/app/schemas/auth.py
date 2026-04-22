import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.auth import OrgPlan, OrgStatus, UserRole


# ─── Organization Schemas ─────────────────────────────────────────────────────
class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    contact_email: EmailStr
    contact_phone: str | None = None
    city: str | None = None
    bin_number: str | None = Field(None, min_length=12, max_length=12)
    locale: str = Field("ru", pattern="^(ru|kk|en)$")
    timezone: str = "Asia/Almaty"


class OrganizationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    plan: OrgPlan
    status: OrgStatus
    contact_email: str
    contact_phone: str | None
    country: str
    city: str | None
    bin_number: str | None
    locale: str
    timezone: str
    max_users: int
    max_documents: int
    created_at: datetime


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    city: str | None = None
    bin_number: str | None = Field(None, min_length=12, max_length=12)
    locale: str | None = Field(None, pattern="^(ru|kk|en)$")
    timezone: str | None = None


# ─── User Schemas ─────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    phone: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    middle_name: str | None
    phone: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    avatar_url: str | None
    organization_id: uuid.UUID | None
    created_at: datetime
    last_login_at: datetime | None

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)


class UserUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    middle_name: str | None = None
    phone: str | None = None
    telegram_chat_id: str | None = None


# ─── Auth Schemas ─────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    """Регистрация новой организации + первого admin-пользователя."""
    # Данные организации
    organization_name: str = Field(..., min_length=2, max_length=255)
    organization_email: EmailStr
    organization_phone: str | None = None
    city: str | None = None
    bin_number: str | None = Field(None, min_length=12, max_length=12)

    # Данные пользователя
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


# ─── Invitation ───────────────────────────────────────────────────────────────
class InviteUserRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.USER
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
