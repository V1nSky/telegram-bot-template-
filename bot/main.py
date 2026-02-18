"""Application entry point.

Supports both polling (development) and webhook (production) modes.

Run::

    python -m bot.main
    # or
    BOT_MODE=webhook python -m bot.main
"""

from __future__ import annotations

import asyncio
import signal
from typing import NoReturn

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot.config import BotMode, settings
from bot.database import create_tables
from bot.handlers import register_handlers
from bot.middlewares import register_middlewares
from bot.utils.logger import configure_logging, get_logger

logger = get_logger(__name__)


async def set_commands(bot: Bot) -> None:
    """Register bot commands in the Telegram menu.

    Args:
        bot: Active :class:`aiogram.Bot` instance.
    """
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="settings", description="Настройки"),
    ])


async def on_startup(bot: Bot) -> None:
    """Actions performed once at startup."""
    await create_tables()
    await set_commands(bot)
    logger.info(
        "bot_started",
        mode=settings.bot_mode.value,
        environment=settings.environment.value,
    )

    if settings.bot_mode == BotMode.webhook and settings.webhook_url:
        await bot.set_webhook(
            url=settings.webhook_url,
            secret_token=settings.webhook_secret.get_secret_value() if settings.webhook_secret else None,
            drop_pending_updates=True,
        )
        logger.info("webhook_set", url=settings.webhook_url)


async def on_shutdown(bot: Bot) -> None:
    """Actions performed once at shutdown."""
    logger.info("bot_stopping")
    if settings.bot_mode == BotMode.webhook:
        await bot.delete_webhook()
    await bot.session.close()
    logger.info("bot_stopped")


def build_dispatcher() -> Dispatcher:
    """Construct and configure the dispatcher.

    Returns:
        Fully configured :class:`aiogram.Dispatcher`.
    """
    dp = Dispatcher()
    register_middlewares(dp)
    register_handlers(dp)
    return dp


async def run_polling() -> None:
    """Start the bot in long-polling mode."""
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    await on_startup(bot)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown(bot)


async def run_webhook() -> None:
    """Start the bot in webhook mode behind an aiohttp web server."""
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    app = web.Application()

    # Health-check endpoint
    async def health(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "mode": "webhook"})

    app.router.add_get("/health", health)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret.get_secret_value() if settings.webhook_secret else None,
    ).register(app, path=settings.webhook_path)

    setup_application(app, dp, bot=bot)

    await on_startup(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.webapp_host, settings.webapp_port)
    await site.start()
    logger.info("webhook_server_started", host=settings.webapp_host, port=settings.webapp_port)

    stop_event = asyncio.Event()

    def _handle_signal() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except (NotImplementedError, RuntimeError):
            pass

    await stop_event.wait()
    await runner.cleanup()
    await on_shutdown(bot)


def main() -> NoReturn:
    """CLI entry-point — select mode from config and run."""
    configure_logging()

    if settings.bot_mode == BotMode.webhook:
        asyncio.run(run_webhook())
    else:
        asyncio.run(run_polling())

    raise SystemExit(0)


if __name__ == "__main__":
    main()
