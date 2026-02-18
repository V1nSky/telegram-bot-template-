"""Unit tests for the UserRepository."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from bot.database.repository import UserRepository
from bot.database.models import UserRole


def _make_tg_user(
    user_id: int = 42,
    username: str = "tester",
    first_name: str = "Test",
    last_name: str | None = "User",
):
    """Helper to build a minimal fake Telegram User."""
    user = MagicMock()
    user.id = user_id
    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.language_code = "en"
    user.is_bot = False
    return user


@pytest.mark.asyncio
async def test_create_user(db_session):
    """UserRepository.create() persists a new user."""
    repo = UserRepository(db_session)
    tg_user = _make_tg_user(user_id=1001)

    user = await repo.create(tg_user)
    await db_session.flush()

    assert user.id is not None
    assert user.telegram_id == 1001
    assert user.username == "tester"
    assert user.role == UserRole.user


@pytest.mark.asyncio
async def test_get_by_telegram_id(db_session):
    """get_by_telegram_id returns the correct user."""
    repo = UserRepository(db_session)
    tg_user = _make_tg_user(user_id=1002)
    await repo.create(tg_user)
    await db_session.flush()

    found = await repo.get_by_telegram_id(1002)
    assert found is not None
    assert found.telegram_id == 1002


@pytest.mark.asyncio
async def test_get_by_telegram_id_missing(db_session):
    """get_by_telegram_id returns None for unknown user."""
    repo = UserRepository(db_session)
    assert await repo.get_by_telegram_id(9999999) is None


@pytest.mark.asyncio
async def test_get_or_create_new(db_session):
    """get_or_create returns (user, True) for a new user."""
    repo = UserRepository(db_session)
    tg_user = _make_tg_user(user_id=2001, username="newbie")

    user, created = await repo.get_or_create(tg_user)
    assert created is True
    assert user.username == "newbie"


@pytest.mark.asyncio
async def test_get_or_create_existing(db_session):
    """get_or_create returns (user, False) for an existing user."""
    repo = UserRepository(db_session)
    tg_user = _make_tg_user(user_id=2002)

    await repo.create(tg_user)
    await db_session.flush()

    _, created = await repo.get_or_create(tg_user)
    assert created is False


@pytest.mark.asyncio
async def test_full_name_with_last_name(db_session):
    """User.full_name includes last name when present."""
    repo = UserRepository(db_session)
    tg_user = _make_tg_user(user_id=3001, first_name="Alice", last_name="Smith")
    user = await repo.create(tg_user)
    await db_session.flush()
    assert user.full_name == "Alice Smith"


@pytest.mark.asyncio
async def test_full_name_without_last_name(db_session):
    """User.full_name is just first name when last_name is absent."""
    repo = UserRepository(db_session)
    tg_user = _make_tg_user(user_id=3002, first_name="Bob", last_name=None)
    user = await repo.create(tg_user)
    await db_session.flush()
    assert user.full_name == "Bob"
