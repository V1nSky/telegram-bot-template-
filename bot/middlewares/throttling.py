"""Throttling (anti-spam) middleware.

Limits how frequently a single user can trigger the bot.
Uses an in-memory TTL cache; swap for Redis-backed storage in production.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, User

from bot.config import settings
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """Drop updates from users that exceed the configured request rate.

    Args:
        rate: Minimum seconds between allowed requests per user.
              Defaults to ``settings.throttle_rate``.

    Example::

        dp.message.middleware(ThrottlingMiddleware(rate=1.0))

    Users that are throttled receive a short informational reply and
    their update is silently dropped from further processing.
    """

    def __init__(self, rate: float | None = None) -> None:
        self._rate = rate if rate is not None else settings.throttle_rate
        self._last_seen: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last_seen.get(user.id, 0.0)

        if now - last < self._rate:
            logger.info("throttled", user_id=user.id)
            if isinstance(event, Message):
                await event.answer("⏳ Слишком много запросов. Подождите немного.")
            return None  # drop update

        self._last_seen[user.id] = now
        return await handler(event, data)
