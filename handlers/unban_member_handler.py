"""
handlers/unban_member_handler.py
Unbans a member from one or all channels and updates their status in Excel.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from handlers.access_control import owner_only
from keyboards.main_menu import back_to_menu_keyboard, cancel_keyboard
from keyboards.channel_keyboards import channel_action_keyboard
from services.utils import parse_identifier


def register(app: Client) -> None:

    @app.on_callback_query(filters.regex(r"^menu:unban_member$"))
    @owner_only
    async def unban_member_start(client: Client, callback_query: CallbackQuery):
        admin_id = callback_query.from_user.id
        client.state_service.set(admin_id, action="unban_member", step="awaiting_identifier")
        await callback_query.message.edit_text(
            "♻ <b>Unban Member</b>\n\nSend the target <b>username</b> or <b>Telegram ID</b>.",
            reply_markup=cancel_keyboard(),
        )
        await callback_query.answer()

    @app.on_message(filters.private & filters.text & filters.create(
        lambda _, c, m: _state_matches(c, m, "unban_member", "awaiting_identifier")
    ))
    @owner_only
    async def unban_member_receive_identifier(client: Client, message: Message):
        admin_id = message.from_user.id
        telegram_id, username = parse_identifier(message.text)

        if telegram_id is None and username is None:
            await message.reply_text("⚠ Invalid input. Send a username or a numeric Telegram ID.")
            return

        client.state_service.update_data(
            admin_id, telegram_id=telegram_id, username=username,
            raw_input=message.text.strip(),
        )
        client.state_service.set_step(admin_id, "awaiting_channel_selection")

        channels = await client.channel_service.get_all()
        if not channels:
            client.state_service.clear(admin_id)
            await message.reply_text("⚠ No channels configured.", reply_markup=back_to_menu_keyboard())
            return

        label = f"@{username}" if username else str(telegram_id)
        await message.reply_text(
            f"Select where to unban <b>{label}</b>:",
            reply_markup=channel_action_keyboard(channels, "unban"),
        )

    @app.on_callback_query(filters.regex(r"^unban_ch:"))
    @owner_only
    async def unban_member_channel_selected(client: Client, callback_query: CallbackQuery):
        admin_id = callback_query.from_user.id
        state = client.state_service.get(admin_id)
        if not state or state.action != "unban_member":
            await callback_query.answer("Session expired. Start again from the menu.", show_alert=True)
            return

        target_channel = callback_query.data.split(":", 1)[1]
        telegram_id = state.data.get("telegram_id")
        username = state.data.get("username")
        raw_input = state.data.get("raw_input", "target user")
        label = f"@{username}" if username else raw_input

        channels_all = await client.channel_service.get_all()
        if target_channel == "__ALL__":
            targets = channels_all
        else:
            targets = [c for c in channels_all if c["name"] == target_channel]

        if not targets:
            await callback_query.answer("Channel not found.", show_alert=True)
            return

        await callback_query.message.edit_text("⏳ Unbanning member...")

        results = []
        for channel in targets:
            success, reason = await client.telegram_service.unban_member(channel["chat_id"], telegram_id)
            if success:
                updated = await client.excel_service.set_member_status(
                    channel["name"], telegram_id=telegram_id, username=username, status="Unbanned"
                )
                note = "" if updated else " (no existing row - not re-added)"
                results.append(f"✅ <b>{channel['name']}</b>: unbanned{note}.")
                status = "unbanned"
            else:
                results.append(f"⚠ <b>{channel['name']}</b>: failed ({reason}).")
                status = f"failed:{reason}"

            await client.excel_service.write_log(
                action="UNBAN", admin=str(admin_id), user=label, channel=channel["name"], status=status,
            )

        client.state_service.clear(admin_id)
        text = f"<b>Unban results for {label}</b>\n\n" + "\n".join(results)
        await callback_query.message.edit_text(text, reply_markup=back_to_menu_keyboard())
        await callback_query.answer()


def _state_matches(client: Client, message: Message, action: str, step: str) -> bool:
    if not hasattr(client, "state_service") or not message.from_user:
        return False
    state = client.state_service.get(message.from_user.id)
    return bool(state and state.action == action and state.step == step)
