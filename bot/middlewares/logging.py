"""Request logging middleware.

Logs every incoming update with user context and processing time.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User

from bot.utils.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Logs each incoming Telegram update.

    Attaches ``user_id``, ``update_type``, and ``processing_ms`` to every
    log record so that structured log aggregators can filter by user.

    Example log output (JSON mode)::

        {"event": "update_processed", "user_id": 123, "update_type": "message",
         "processing_ms": 42, "level": "info"}
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        start = time.perf_counter()

        user: User | None = data.get("event_from_user")
        update: Update | None = data.get("event_update")

        update_type = "unknown"
        if update:
            for field in ("message", "callback_query", "inline_query", "edited_message"):
                if getattr(update, field, None):
                    update_type = field
                    break

        log = logger.bind(
            user_id=user.id if user else None,
            username=user.username if user else None,
            update_type=update_type,
        )
        log.debug("update_received")

        try:
            result = await handler(event, data)
            elapsed_ms = round((time.perf_counter() - start) * 1000)
            log.info("update_processed", processing_ms=elapsed_ms)
            return result
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000)
            log.exception("update_failed", processing_ms=elapsed_ms, error=str(exc))
            raise
