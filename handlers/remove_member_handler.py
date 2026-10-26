"""
handlers/remove_member_handler.py
Bans a member from one or all channels and deletes their row from Excel.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from handlers.access_control import owner_only
from keyboards.main_menu import back_to_menu_keyboard, cancel_keyboard
from keyboards.channel_keyboards import channel_action_keyboard
from services.utils import parse_identifier


def register(app: Client) -> None:

    @app.on_callback_query(filters.regex(r"^menu:remove_member$"))
    @owner_only
    async def remove_member_start(client: Client, callback_query: CallbackQuery):
        admin_id = callback_query.from_user.id
        client.state_service.set(admin_id, action="remove_member", step="awaiting_identifier")
        await callback_query.message.edit_text(
            "➖ <b>Remove Member</b>\n\nSend the target <b>username</b> or <b>Telegram ID</b>.",
            reply_markup=cancel_keyboard(),
        )
        await callback_query.answer()

    @app.on_message(filters.private & filters.text & filters.create(
        lambda _, c, m: _state_matches(c, m, "remove_member", "awaiting_identifier")
    ))
    @owner_only
    async def remove_member_receive_identifier(client: Client, message: Message):
        admin_id = message.from_user.id
        telegram_id, username = parse_identifier(message.text)

        if telegram_id is None and username is None:
            await message.reply_text("⚠ Invalid input. Send a username or a numeric Telegram ID.")
            return

        matches = await client.excel_service.find_member(telegram_id=telegram_id, username=username)
        if not matches:
            client.state_service.clear(admin_id)
            await message.reply_text(
                "⚠ No matching member found in any channel.",
                reply_markup=back_to_menu_keyboard(),
            )
            return

        resolved_id = matches[0]["telegram_id"]
        resolved_username = matches[0]["username"] or username

        client.state_service.update_data(
            admin_id, telegram_id=resolved_id, username=resolved_username,
            raw_input=message.text.strip(),
        )
        client.state_service.set_step(admin_id, "awaiting_channel_selection")

        present_channels = [{"name": m["channel"]} for m in matches]
        label = f"@{resolved_username}" if resolved_username else str(resolved_id)
        await message.reply_text(
            f"Found <b>{label}</b> in {len(matches)} channel(s). Select where to remove them:",
            reply_markup=channel_action_keyboard(present_channels, "remove"),
        )

    @app.on_callback_query(filters.regex(r"^remove_ch:"))
    @owner_only
    async def remove_member_channel_selected(client: Client, callback_query: CallbackQuery):
        admin_id = callback_query.from_user.id
        state = client.state_service.get(admin_id)
        if not state or state.action != "remove_member":
            await callback_query.answer("Session expired. Start again from the menu.", show_alert=True)
            return

        target_channel = callback_query.data.split(":", 1)[1]
        telegram_id = state.data.get("telegram_id")
        username = state.data.get("username")
        raw_input = state.data.get("raw_input", "target user")
        label = f"@{username}" if username else raw_input

        matches = await client.excel_service.find_member(telegram_id=telegram_id, username=username)
        if target_channel == "__ALL__":
            channel_names = [m["channel"] for m in matches]
        else:
            channel_names = [target_channel] if any(m["channel"] == target_channel for m in matches) else []

        if not channel_names:
            await callback_query.answer("Member not found in that channel.", show_alert=True)
            return

        await callback_query.message.edit_text("⏳ Removing member...")

        results = []
        for channel_name in channel_names:
            channel = await client.channel_service.get_by_name(channel_name)
            if not channel:
                results.append(f"⚠ <b>{channel_name}</b>: channel config missing, skipped.")
                continue

            success, reason = await client.telegram_service.ban_member(channel["chat_id"], telegram_id)
            if success:
                await client.excel_service.remove_member(channel_name, telegram_id=telegram_id, username=username)
                results.append(f"✅ <b>{channel_name}</b>: banned and removed from database.")
                status = "banned"
            else:
                results.append(f"⚠ <b>{channel_name}</b>: failed ({reason}).")
                status = f"failed:{reason}"

            await client.excel_service.write_log(
                action="REMOVE", admin=str(admin_id), user=label, channel=channel_name, status=status,
            )

        client.state_service.clear(admin_id)
        text = f"<b>Remove results for {label}</b>\n\n" + "\n".join(results)
        await callback_query.message.edit_text(text, reply_markup=back_to_menu_keyboard())
        await callback_query.answer()


def _state_matches(client: Client, message: Message, action: str, step: str) -> bool:
    if not hasattr(client, "state_service") or not message.from_user:
        return False
    state = client.state_service.get(message.from_user.id)
    return bool(state and state.action == action and state.step == step)
