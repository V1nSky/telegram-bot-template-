"""Integration tests for command handlers."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.commands import cmd_help, cmd_settings, cmd_start


@pytest.mark.asyncio
async def test_cmd_help_replies(make_message):
    """cmd_help sends a message containing available commands."""
    msg = make_message("/help")
    await cmd_help(msg)
    msg.answer.assert_awaited_once()
    call_args = msg.answer.call_args[0][0]
    assert "/start" in call_args
    assert "/help" in call_args


@pytest.mark.asyncio
async def test_cmd_settings_replies(make_message):
    """/settings handler sends a reply."""
    msg = make_message("/settings")
    await cmd_settings(msg)
    msg.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cmd_start_no_from_user():
    """/start with no from_user exits gracefully."""
    msg = MagicMock()
    msg.from_user = None
    msg.answer = AsyncMock()
    await cmd_start(msg)
    msg.answer.assert_not_awaited()


@pytest.mark.asyncio
async def test_cmd_start_creates_user(make_message):
    """/start creates a new user and sends a greeting."""
    from bot.database.models import User, UserRole
    from datetime import datetime

    fake_user = MagicMock(spec=User)
    fake_user.full_name = "Test User"
    fake_user.telegram_id = 111222333
    fake_user.role = UserRole.user
    fake_user.created_at = datetime.utcnow()

    msg = make_message("/start")

    with patch("bot.handlers.commands.AsyncSessionFactory") as mock_factory, \
         patch("bot.handlers.commands.UserRepository") as mock_repo_cls:

        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_repo = AsyncMock()
        mock_repo.get_or_create = AsyncMock(return_value=(fake_user, True))
        mock_repo_cls.return_value = mock_repo

        await cmd_start(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Test User" in text
    assert "Добро пожаловать" in text
