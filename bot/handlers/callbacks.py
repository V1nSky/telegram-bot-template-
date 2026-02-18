"""Callback query handlers for inline keyboards.

Patterns follow the ``"prefix:action[:payload]"`` convention used by
:mod:`bot.keyboards.inline`.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.database import AsyncSessionFactory
from bot.database.repository import UserRepository
from bot.keyboards.inline import back_kb, main_menu_kb
from bot.utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="callbacks")


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery) -> None:
    """Return to the main menu."""
    await callback.message.edit_text(  # type: ignore[union-attr]
        "Главное меню:",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def cb_profile(callback: CallbackQuery) -> None:
    """Show user profile info."""
    if callback.from_user is None:
        await callback.answer()
        return

    async with AsyncSessionFactory() as session:
        user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"Имя: {user.full_name}\n"
        f"Username: @{user.username or '—'}\n"
        f"Роль: {user.role.value}\n"
        f"В боте с: {user.created_at.strftime('%d.%m.%Y')}"
    )
    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        reply_markup=back_kb("menu:main"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery) -> None:
    """Inline help screen."""
    text = (
        "❓ <b>Помощь</b>\n\n"
        "Используйте кнопки меню для навигации.\n"
        "<i>Добавьте сюда описание возможностей бота.</i>"
    )
    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        reply_markup=back_kb("menu:main"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def cb_settings(callback: CallbackQuery) -> None:
    """Inline settings placeholder."""
    await callback.message.edit_text(  # type: ignore[union-attr]
        "⚙️ <b>Настройки</b>\n\n<i>Реализуйте под свою задачу.</i>",
        reply_markup=back_kb("menu:main"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:"))
async def cb_confirm(callback: CallbackQuery) -> None:
    """Generic yes/no confirmation handler.

    Callback data format: ``"confirm:{yes|no}:{action}"``.
    """
    _, choice, action = (callback.data or "").split(":", 2)
    logger.info("confirm_callback", choice=choice, action=action, user_id=callback.from_user and callback.from_user.id)

    if choice == "yes":
        # TODO: dispatch to action-specific logic
        await callback.answer(f"Действие '{action}' подтверждено", show_alert=False)
    else:
        await callback.answer("Отменено")


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    """No-op handler for decorative buttons (e.g. page counter)."""
    await callback.answer()
