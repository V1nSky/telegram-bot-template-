"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force test environment before any bot imports
os.environ.setdefault("BOT_TOKEN", "0:fake_token_for_tests")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "development")

from bot.database.models import Base  # noqa: E402
from bot.handlers import register_handlers  # noqa: E402
from bot.middlewares import register_middlewares  # noqa: E402


# ── Database ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def engine():
    """In-memory SQLite engine shared across the test session."""
    return create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)


@pytest.fixture(scope="session")
async def create_db(engine):
    """Create all tables once per test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(engine, create_db) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test."""
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


# ── Bot / Dispatcher ──────────────────────────────────────────────────────────

@pytest.fixture
def bot() -> Bot:
    """Return a Bot instance with a mocked session."""
    mock_bot = MagicMock(spec=Bot)
    mock_bot.id = 123456789
    mock_bot.token = "0:fake_token_for_tests"
    mock_bot.send_message = AsyncMock(return_value=MagicMock())
    mock_bot.answer = AsyncMock()
    return mock_bot


@pytest.fixture
def dp() -> Dispatcher:
    """Return a configured Dispatcher for handler tests."""
    dispatcher = Dispatcher()
    register_middlewares(dispatcher)
    register_handlers(dispatcher)
    return dispatcher


# ── Telegram objects ──────────────────────────────────────────────────────────

@pytest.fixture
def tg_user():
    """Return a fake aiogram User object."""
    from aiogram.types import User
    return User(
        id=111222333,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="ru",
    )


@pytest.fixture
def make_message(tg_user, bot):
    """Factory for creating fake Message objects."""
    def _make(text: str = "/start", chat_id: int = 111222333) -> MagicMock:
        from aiogram.types import Chat, Message
        msg = MagicMock(spec=Message)
        msg.from_user = tg_user
        msg.chat = MagicMock(spec=Chat)
        msg.chat.id = chat_id
        msg.text = text
        msg.answer = AsyncMock()
        msg.reply = AsyncMock()
        return msg
    return _make
