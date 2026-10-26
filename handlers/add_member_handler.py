"""
handlers/add_member_handler.py

Telegram's Bot API/MTProto rules do not allow a bot to silently insert an
arbitrary user into a channel. The only supported path is:

    1. Bot creates a single-use invite link for the target channel.
    2. Admin forwards that link to the user (or the bot sends it directly
       if the user has already started a conversation with the bot).
    3. When the user joins through that link, Telegram fires a
       ChatMemberUpdated event (handled in handlers/join_handler.py),
       which is what actually writes the member into the Excel sheet.

This handler therefore never attempts an unsupported "force add" call -
it only ever creates and hands out invite links, exactly as required.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from handlers.access_control import owner_only
from keyboards.main_menu import back_to_menu_keyboard, cancel_keyboard
from keyboards.channel_keyboards import channel_action_keyboard
from services.utils import parse_identifier
from services.i18n import t, lang


def register(app: Client) -> None:

    @app.on_callback_query(filters.regex(r"^menu:add_member$"))
    @owner_only
    async def add_member_start(client: Client, callback_query: CallbackQuery):
        admin_id = callback_query.from_user.id
        client.state_service.set(admin_id, action="add_member", step="awaiting_identifier")
        await callback_query.message.edit_text(
            t(client, admin_id, "add_member_prompt"),
            reply_markup=cancel_keyboard(lang(client, admin_id)),
        )
        await callback_query.answer()

    @app.on_message(filters.private & filters.text & filters.create(
        lambda _, c, m: _state_matches(c, m, "add_member", "awaiting_identifier")
    ))
    @owner_only
    async def add_member_receive_identifier(client: Client, message: Message):
        admin_id = message.from_user.id
        telegram_id, username = parse_identifier(message.text)

        if telegram_id is None and username is None:
            await message.reply_text(t(client, admin_id, "invalid_input"))
            return

        full_name = None
        resolved_id = telegram_id
        if client.telegram_service:
            identifier = telegram_id if telegram_id is not None else f"@{username}"
            resolved = await client.telegram_service.resolve_user(identifier)
            if resolved:
                resolved_id = resolved["id"]
                username = resolved["username"] or username
                full_name = resolved["full_name"]

        client.state_service.update_data(
            admin_id,
            telegram_id=resolved_id,
            username=username,
            full_name=full_name,
            raw_input=message.text.strip(),
        )
        client.state_service.set_step(admin_id, "awaiting_channel_selection")

        channels = await client.channel_service.get_enabled()
        if not channels:
            client.state_service.clear(admin_id)
            await message.reply_text(
                t(client, admin_id, "no_enabled_channels"),
                reply_markup=back_to_menu_keyboard(lang(client, admin_id)),
            )
            return

        label = f"@{username}" if username else str(resolved_id)
        await message.reply_text(
            t(client, admin_id, "select_channel", label=label),
            reply_markup=channel_action_keyboard(channels, "add", language=lang(client, admin_id)),
        )

    @app.on_callback_query(filters.regex(r"^add_ch:"))
    @owner_only
    async def add_member_channel_selected(client: Client, callback_query: CallbackQuery):
        admin_id = callback_query.from_user.id
        state = client.state_service.get(admin_id)
        if not state or state.action != "add_member":
            await callback_query.answer(t(client, admin_id, "session_expired"), show_alert=True)
            return

        target_channel = callback_query.data.split(":", 1)[1]
        username = state.data.get("username")
        raw_input = state.data.get("raw_input", "target user")
        label = f"@{username}" if username else raw_input

        channels_all = await client.channel_service.get_enabled()
        if target_channel == "__ALL__":
            targets = channels_all
        else:
            targets = [c for c in channels_all if c["name"] == target_channel]

        if not targets:
            await callback_query.answer(t(client, admin_id, "channel_missing"), show_alert=True)
            return

        await callback_query.message.edit_text(t(client, admin_id, "generating"))

        results = []
        for channel in targets:
            link = await client.telegram_service.create_single_use_invite_link(
                channel["chat_id"], name=f"invite-{label}"
            )
            if link:
                results.append((channel["name"], f"📢 <b>{channel['name']}</b>\n{link}"))
                await client.excel_service.write_log(
                    action="ADD",
                    admin=str(admin_id),
                    user=label,
                    channel=channel["name"],
                    status="invite_generated",
                )
            else:
                results.append((channel["name"], f"📢 <b>{channel['name']}</b>\n{t(client, admin_id, 'failed_link')}"))
                await client.excel_service.write_log(
                    action="ADD",
                    admin=str(admin_id),
                    user=label,
                    channel=channel["name"],
                    status="failed",
                )

        client.state_service.clear(admin_id)

        await callback_query.message.edit_text(
            t(client, admin_id, "link_ready", label=label) + "\n" + t(client, admin_id, "send_links"),
            reply_markup=back_to_menu_keyboard(lang(client, admin_id)),
        )
        # Deliberately send one message per channel so each link is clearly separated.
        for channel_name, result in results:
            await callback_query.message.reply_text(result)
        await callback_query.answer()


def _state_matches(client: Client, message: Message, action: str, step: str) -> bool:
    if not hasattr(client, "state_service") or not message.from_user:
        return False
    state = client.state_service.get(message.from_user.id)
    return bool(state and state.action == action and state.step == step)
