"""
handlers/search_member_handler.py
Searches every channel sheet for a member and displays where they were found.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from handlers.access_control import owner_only
from keyboards.main_menu import back_to_menu_keyboard, cancel_keyboard
from keyboards.channel_keyboards import search_result_keyboard
from services.utils import parse_identifier, format_member_line


def register(app: Client) -> None:

    @app.on_callback_query(filters.regex(r"^menu:search_member$"))
    @owner_only
    async def search_member_start(client: Client, callback_query: CallbackQuery):
        admin_id = callback_query.from_user.id
        client.state_service.set(admin_id, action="search_member", step="awaiting_identifier")
        await callback_query.message.edit_text(
            "🔍 <b>Search Member</b>\n\nSend a <b>username</b> or <b>Telegram ID</b> to search.",
            reply_markup=cancel_keyboard(),
        )
        await callback_query.answer()

    @app.on_message(filters.private & filters.text & filters.create(
        lambda _, c, m: _state_matches(c, m, "search_member", "awaiting_identifier")
    ))
    @owner_only
    async def search_member_receive_identifier(client: Client, message: Message):
        admin_id = message.from_user.id
        telegram_id, username = parse_identifier(message.text)

        if telegram_id is None and username is None:
            await message.reply_text("⚠ Invalid input. Send a username or a numeric Telegram ID.")
            return

        client.state_service.clear(admin_id)
        matches = await client.excel_service.find_member(telegram_id=telegram_id, username=username)

        if not matches:
            await message.reply_text(
                "❌ No matching member found in any channel.",
                reply_markup=back_to_menu_keyboard(),
            )
            return

        body = "\n\n".join(format_member_line(m) for m in matches)
        await message.reply_text(
            f"🔍 <b>Found in {len(matches)} channel(s)</b>\n\n{body}",
            reply_markup=search_result_keyboard(matches),
        )


def _state_matches(client: Client, message: Message, action: str, step: str) -> bool:
    if not hasattr(client, "state_service") or not message.from_user:
        return False
    state = client.state_service.get(message.from_user.id)
    return bool(state and state.action == action and state.step == step)
