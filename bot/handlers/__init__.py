"""Handler registry — import and include all routers here."""

from __future__ import annotations

from aiogram import Dispatcher

from bot.handlers.callbacks import router as callbacks_router
from bot.handlers.commands import router as commands_router
from bot.handlers.messages import router as messages_router


def register_handlers(dp: Dispatcher) -> None:
    """Include all handler routers into *dp*.

    Order matters: more specific routers first.

    Args:
        dp: Active :class:`aiogram.Dispatcher`.
    """
    dp.include_router(commands_router)
    dp.include_router(callbacks_router)
    dp.include_router(messages_router)  # fallback — must be last


__all__ = ["register_handlers"]
