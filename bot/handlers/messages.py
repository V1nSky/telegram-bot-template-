"""Free-text message handlers.

Catches messages that don't match any command or FSM state.
Extend this with your own FSM states and text filters.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.inline import main_menu_kb

router = Router(name="messages")


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """Echo handler — fallback for unrecognised text input.

    Replace or extend this with your business logic or FSM states.

    Args:
        message: Incoming text message.
    """
    await message.answer(
        f"Вы написали: <i>{message.text}</i>\n\n"
        "Я не знаю, как ответить на это. "
        "Воспользуйтесь меню или командой /help.",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )
