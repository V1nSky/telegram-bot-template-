"""Command handlers: /start, /help, /settings.

Add your own commands by following the pattern in this file.

How to add a new command
------------------------
1. Define an async handler function that accepts ``Message`` and ``**kwargs``.
2. Register it with ``@router.message(Command("mycommand"))``.
3. Import this router in ``bot/handlers/__init__.py`` (already done automatically).
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.database import AsyncSessionFactory
from bot.database.repository import UserRepository
from bot.keyboards.inline import main_menu_kb
from bot.utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="commands")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """/start — greet the user and persist them in the database.

    Args:
        message: Incoming Telegram message.
    """
    if message.from_user is None:
        return

    async with AsyncSessionFactory() as session:
        repo = UserRepository(session)
        user, created = await repo.get_or_create(message.from_user)
        await session.commit()

    greeting = "Добро пожаловать" if created else "С возвращением"
    logger.info("start_command", user_id=message.from_user.id, new_user=created)

    await message.answer(
        f"{greeting}, <b>{user.full_name}</b>! 👋\n\n"
        "Я готов к работе. Выберите действие:",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """/help — show available commands.

    Args:
        message: Incoming Telegram message.
    """
    help_text = (
        "<b>Доступные команды:</b>\n\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/settings — настройки\n\n"
        "<i>Добавьте сюда описание ваших команд.</i>"
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    """/settings — placeholder for user preferences.

    Args:
        message: Incoming Telegram message.
    """
    await message.answer(
        "⚙️ <b>Настройки</b>\n\n"
        "Здесь будут ваши настройки.\n"
        "<i>Реализуйте этот раздел под свою задачу.</i>",
        parse_mode="HTML",
    )
