"""Inline keyboard factories.

All keyboards are created via factory functions that return
:class:`aiogram.types.InlineKeyboardMarkup`.

Example::

    await message.answer("Выберите действие:", reply_markup=main_menu_kb())
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    """Return the main menu inline keyboard.

    Returns:
        Keyboard with Profile, Help, and Settings buttons.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="menu:profile"),
        InlineKeyboardButton(text="❓ Помощь", callback_data="menu:help"),
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings"),
    )
    return builder.as_markup()


def confirm_kb(action: str) -> InlineKeyboardMarkup:
    """Return a Yes / No confirmation keyboard.

    Args:
        action: Action identifier embedded in callback data.

    Returns:
        Two-button keyboard for confirmation dialogs.

    Example::

        kb = confirm_kb("delete_account")
        await message.answer("Удалить аккаунт?", reply_markup=kb)
        # callback_data will be "confirm:yes:delete_account" / "confirm:no:delete_account"
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:yes:{action}"),
        InlineKeyboardButton(text="❌ Нет", callback_data=f"confirm:no:{action}"),
    )
    return builder.as_markup()


def back_kb(target: str = "menu:main") -> InlineKeyboardMarkup:
    """Return a single «Back» button.

    Args:
        target: Callback data for the back button. Defaults to ``"menu:main"``.
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=target))
    return builder.as_markup()


def paginate_kb(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Return pagination controls.

    Args:
        page: Current page (0-indexed).
        total_pages: Total number of pages.
        prefix: Callback prefix, e.g. ``"items"``.
                Buttons emit ``"{prefix}:page:{n}"`` callbacks.
    """
    builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    if page > 0:
        buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"{prefix}:page:{page - 1}"))
    buttons.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
    )
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"{prefix}:page:{page + 1}"))

    builder.row(*buttons)
    return builder.as_markup()
