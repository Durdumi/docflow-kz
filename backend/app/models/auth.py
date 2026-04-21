"""
Модели PUBLIC схемы — системные таблицы.
Данные документов/отчётов хранятся в schema каждого тенанта.
"""
import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ─── Enums ────────────────────────────────────────────────────────────────────
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"   # Администратор платформы
    ORG_ADMIN = "org_admin"       # Администратор организации
    MANAGER = "manager"           # Менеджер (создаёт и просматривает)
    USER = "user"                 # Обычный пользователь


class OrgPlan(str, Enum):
    FREE = "free"           # До 5 пользователей, 100 документов
    STARTER = "starter"     # До 20 пользователей
    BUSINESS = "business"   # До 100 пользователей
    ENTERPRISE = "enterprise"


class OrgStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


# ─── Mixins ───────────────────────────────────────────────────────────────────
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


# ─── Organization ─────────────────────────────────────────────────────────────
class Organization(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    schema_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    plan: Mapped[OrgPlan] = mapped_column(
        String(50), default=OrgPlan.TRIAL, nullable=False
    )
    status: Mapped[OrgStatus] = mapped_column(
        String(50), default=OrgStatus.TRIAL, nullable=False
    )

    # Контактная информация
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str] = mapped_column(String(10), default="KZ")
    city: Mapped[str | None] = mapped_column(String(100))
    bin_number: Mapped[str | None] = mapped_column(String(12))  # БИН организации

    # Настройки
    max_users: Mapped[int] = mapped_column(Integer, default=5)
    max_documents: Mapped[int] = mapped_column(Integer, default=100)
    locale: Mapped[str] = mapped_column(String(10), default="ru")  # ru / kk / en
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Almaty")

    # Отношения
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        "OrganizationMembership", back_populates="organization"
    )

    def __repr__(self) -> str:
        return f"<Organization {self.slug}>"


# ─── User ─────────────────────────────────────────────────────────────────────
class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100))  # Отчество

    phone: Mapped[str | None] = mapped_column(String(50))
    avatar_url: Mapped[str | None] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Текущая организация (основная)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    role: Mapped[UserRole] = mapped_column(String(50), default=UserRole.USER)

    # Telegram
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50))

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Отношения
    organization: Mapped["Organization | None"] = relationship(
        "Organization", back_populates="users"
    )
    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        "OrganizationMembership", back_populates="user"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# ─── OrganizationMembership ───────────────────────────────────────────────────
class OrganizationMembership(UUIDMixin, TimestampMixin, Base):
    """Пользователь может быть членом нескольких организаций."""
    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_org"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE")
    )
    role: Mapped[UserRole] = mapped_column(String(50), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    invited_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    user: Mapped["User"] = relationship("User", back_populates="memberships")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="memberships"
    )


# ─── RefreshToken ─────────────────────────────────────────────────────────────
class RefreshToken(UUIDMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at
