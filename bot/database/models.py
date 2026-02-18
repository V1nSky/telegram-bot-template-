"""ORM models for the bot.

Contains User and Session models. Extend this file to add domain entities.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base."""


class UserRole(str, enum.Enum):
    """Available user roles."""

    user = "user"
    moderator = "moderator"
    admin = "admin"


class User(Base):
    """Telegram user persisted in the database.

    Created on first ``/start`` interaction.

    Attributes:
        id: Internal surrogate key.
        telegram_id: Unique Telegram user ID.
        username: Optional @username (without ``@``).
        first_name: First name from Telegram profile.
        last_name: Last name from Telegram profile.
        language_code: IETF language tag (e.g. ``"ru"``).
        is_bot: Whether the account is a bot.
        is_active: Soft-delete flag.
        role: Access level.
        created_at: Timestamp of first interaction.
        updated_at: Timestamp of last update.
        sessions: Related :class:`Session` objects.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.user, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Human-readable display name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id} username={self.username!r}>"


class Session(Base):
    """Tracks per-user bot session metadata.

    Useful for analytics, rate-limiting, and resumable state.

    Attributes:
        id: Internal surrogate key.
        user_id: FK to :class:`User`.
        state: Current FSM state name (optional).
        data: Serialised session payload (JSON string).
        is_active: Whether the session is currently open.
        started_at: When the session began.
        last_seen_at: Timestamp of the most recent interaction.
        user: Owning :class:`User`.
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session id={self.id} user_id={self.user_id} state={self.state!r}>"
