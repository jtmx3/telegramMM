"""
handlers/access_control.py
Restricts every interaction to a single owner account.
"""

from functools import wraps

from pyrogram import Client
from pyrogram.types import Message, CallbackQuery

from config import OWNER_ID, PERMISSION_DENIED_MESSAGE
from services.log_service import LogService

_fallback_log_service = LogService()


def _sender_id(update) -> int | None:
    if isinstance(update, Message):
        return update.from_user.id if update.from_user else None
    if isinstance(update, CallbackQuery):
        return update.from_user.id if update.from_user else None
    return None


def owner_only(handler):
    """Decorator for Pyrogram handlers - only OWNER_ID may proceed."""

    @wraps(handler)
    async def wrapper(client: Client, update, *args, **kwargs):
        sender_id = _sender_id(update)

        if sender_id != OWNER_ID:
            if isinstance(update, Message):
                await update.reply_text(PERMISSION_DENIED_MESSAGE)
            elif isinstance(update, CallbackQuery):
                await update.answer(PERMISSION_DENIED_MESSAGE, show_alert=True)
            return

        try:
            return await handler(client, update, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - a handler bug must never crash the bot
            log_service = getattr(client, "log_service", _fallback_log_service)
            log_service.error(f"Unhandled exception in handler '{handler.__name__}'", exc)
            try:
                if isinstance(update, Message):
                    await update.reply_text("⚠ An unexpected error occurred. It has been logged.")
                elif isinstance(update, CallbackQuery):
                    await update.answer("⚠ An unexpected error occurred. It has been logged.", show_alert=True)
            except Exception:  # noqa: BLE001 - never let error reporting itself crash the bot
                pass

    return wrapper
