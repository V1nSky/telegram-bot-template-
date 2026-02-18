"""Repository layer — all DB access goes through these classes.

Usage::

    async with AsyncSessionFactory() as session:
        repo = UserRepository(session)
        user = await repo.get_or_create(tg_user)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from aiogram.types import User as TelegramUser
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Session, User, UserRole


class UserRepository:
    """CRUD operations for :class:`~bot.database.models.User`.

    Args:
        session: Active async SQLAlchemy session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Fetch a user by their Telegram ID.

        Args:
            telegram_id: Numeric Telegram user ID.

        Returns:
            :class:`User` instance or ``None`` if not found.
        """
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch a user by internal primary key."""
        return await self._session.get(User, user_id)

    async def create(self, tg_user: TelegramUser) -> User:
        """Persist a new user from a Telegram ``User`` object.

        Args:
            tg_user: Telegram user object from an incoming update.

        Returns:
            Newly created and flushed :class:`User`.
        """
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            language_code=tg_user.language_code,
            is_bot=tg_user.is_bot,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_or_create(self, tg_user: TelegramUser) -> tuple[User, bool]:
        """Fetch existing user or create a new one.

        Args:
            tg_user: Telegram user from an update.

        Returns:
            A ``(user, created)`` tuple where *created* is ``True``
            when the row was inserted.
        """
        user = await self.get_by_telegram_id(tg_user.id)
        if user:
            # Sync mutable profile fields
            user.username = tg_user.username
            user.first_name = tg_user.first_name
            user.last_name = tg_user.last_name
            user.language_code = tg_user.language_code
            await self._session.flush()
            return user, False
        return await self.create(tg_user), True

    async def set_role(self, telegram_id: int, role: UserRole) -> None:
        """Change a user's role.

        Args:
            telegram_id: Target user's Telegram ID.
            role: New role to assign.
        """
        await self._session.execute(
            update(User).where(User.telegram_id == telegram_id).values(role=role)
        )

    async def deactivate(self, telegram_id: int) -> None:
        """Soft-delete a user (sets ``is_active=False``)."""
        await self._session.execute(
            update(User).where(User.telegram_id == telegram_id).values(is_active=False)
        )

    async def count_active(self) -> int:
        """Return the total number of active users."""
        from sqlalchemy import func, select as sa_select

        result = await self._session.execute(
            sa_select(func.count()).select_from(User).where(User.is_active.is_(True))
        )
        return result.scalar_one()


class SessionRepository:
    """CRUD operations for :class:`~bot.database.models.Session`.

    Args:
        session: Active async SQLAlchemy session.
    """

    def __init__(self, db_session: AsyncSession) -> None:
        self._session = db_session

    async def get_active(self, user_id: int) -> Optional[Session]:
        """Return the latest active session for a user."""
        result = await self._session.execute(
            select(Session)
            .where(Session.user_id == user_id, Session.is_active.is_(True))
            .order_by(Session.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int) -> Session:
        """Open a new session for *user_id*."""
        sess = Session(user_id=user_id)
        self._session.add(sess)
        await self._session.flush()
        return sess

    async def update_state(self, session_id: int, state: Optional[str], data: Optional[str] = None) -> None:
        """Persist FSM state into the session row."""
        values: dict = {"state": state, "last_seen_at": datetime.utcnow()}
        if data is not None:
            values["data"] = data
        await self._session.execute(
            update(Session).where(Session.id == session_id).values(**values)
        )

    async def close(self, session_id: int) -> None:
        """Mark a session as closed."""
        await self._session.execute(
            update(Session).where(Session.id == session_id).values(is_active=False)
        )
