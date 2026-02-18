"""Middleware registration helpers."""

from __future__ import annotations

from aiogram import Dispatcher

from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware


def register_middlewares(dp: Dispatcher) -> None:
    """Attach all middlewares to *dp* in correct order.

    Args:
        dp: Active :class:`aiogram.Dispatcher` instance.
    """
    dp.update.outer_middleware(LoggingMiddleware())
    dp.message.middleware(ThrottlingMiddleware())


__all__ = ["register_middlewares", "LoggingMiddleware", "ThrottlingMiddleware"]
