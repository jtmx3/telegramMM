"""
handlers/channels_handler.py
Full channel management: add, delete, enable, disable, refresh.
Everything is persisted to channels.json - no channel is ever hardcoded.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from handlers.access_control import owner_only
from keyboards.main_menu import back_to_menu_keyboard, cancel_keyboard
from keyboards.channel_keyboards import (
    channel_management_keyboard,
    channel_detail_keyboard,
)


def register(app: Client) -> None:

    # ------------------------------------------------------------------
    # Channel list / management root
    # ------------------------------------------------------------------
    @app.on_callback_query(filters.regex(r"^menu:channels$"))
    @owner_only
    async def channels_menu(client: Client, callback_query: CallbackQuery):
        client.state_service.clear(callback_query.from_user.id)
        channels = await client.channel_service.get_all()
        text = "📢 <b>Channels</b>\n\n" + (
            "\n".join(f"{'🟢' if c.get('enabled', True) else '🔴'} {c['name']}" for c in channels)
            if channels else "No channels configured yet."
        )
        await callback_query.message.edit_text(text, reply_markup=channel_management_keyboard(channels))
        await callback_query.answer()

    @app.on_callback_query(filters.regex(r"^chinfo:"))
    @owner_only
    async def channel_info(client: Client, callback_query: CallbackQuery):
        name = callback_query.data.split(":", 1)[1]
        channel = await client.channel_service.get_by_name(name)
        if not channel:
            await callback_query.answer("Channel not found.", show_alert=True)
            return

        text = (
            f"📢 <b>{channel['name']}</b>\n\n"
            f"Chat ID: <code>{channel['chat_id']}</code>\n"
            f"Invite Link: {channel.get('invite_link') or '—'}\n"
            f"Status: {'🟢 Enabled' if channel.get('enabled', True) else '🔴 Disabled'}"
        )
        await callback_query.message.edit_text(
            text, reply_markup=channel_detail_keyboard(channel["name"], channel.get("enabled", True))
        )
        await callback_query.answer()

    # ------------------------------------------------------------------
    # Enable / Disable
    # ------------------------------------------------------------------
    @app.on_callback_query(filters.regex(r"^chtoggle:"))
    @owner_only
    async def channel_toggle(client: Client, callback_query: CallbackQuery):
        _, action, name = callback_query.data.split(":", 2)
        enabled = action == "enable"
        ok = await client.channel_service.set_enabled(name, enabled)
        if not ok:
            await callback_query.answer("Channel not found.", show_alert=True)
            return

        await client.excel_service.write_log(
            action="ENABLE" if enabled else "DISABLE",
            admin=str(callback_query.from_user.id),
            user="-",
            channel=name,
            status="ok",
        )
        channel = await client.channel_service.get_by_name(name)
        text = (
            f"📢 <b>{channel['name']}</b>\n\n"
            f"Chat ID: <code>{channel['chat_id']}</code>\n"
            f"Invite Link: {channel.get('invite_link') or '—'}\n"
            f"Status: {'🟢 Enabled' if channel.get('enabled', True) else '🔴 Disabled'}"
        )
        await callback_query.message.edit_text(
            text, reply_markup=channel_detail_keyboard(channel["name"], channel.get("enabled", True))
        )
        await callback_query.answer(f"Channel {'enabled' if enabled else 'disabled'}.")

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------
    @app.on_callback_query(filters.regex(r"^chmenu:delete$"))
    @owner_only
    async def channel_delete_menu(client: Client, callback_query: CallbackQuery):
        channels = await client.channel_service.get_all()
        if not channels:
            await callback_query.answer("No channels to delete.", show_alert=True)
            return
        from keyboards.channel_keyboards import delete_channel_select_keyboard
        await callback_query.message.edit_text(
            "🗑 <b>Delete Channel</b>\n\nSelect a channel to remove:",
            reply_markup=delete_channel_select_keyboard(channels),
        )
        await callback_query.answer()

    @app.on_callback_query(filters.regex(r"^chdelete:"))
    @owner_only
    async def channel_delete_confirm(client: Client, callback_query: CallbackQuery):
        name = callback_query.data.split(":", 1)[1]
        ok = await client.channel_service.delete_channel(name)
        if not ok:
            await callback_query.answer("Channel not found.", show_alert=True)
            return

        await client.excel_service.write_log(
            action="DELETE_CHANNEL", admin=str(callback_query.from_user.id), user="-", channel=name, status="ok",
        )

        channels = await client.channel_service.get_all()
        text = f"✅ Channel <b>{name}</b> deleted from configuration.\n\n📢 <b>Channels</b>\n\n" + (
            "\n".join(f"{'🟢' if c.get('enabled', True) else '🔴'} {c['name']}" for c in channels)
            if channels else "No channels configured yet."
        )
        await callback_query.message.edit_text(text, reply_markup=channel_management_keyboard(channels))
        await callback_query.answer("Channel deleted.")

    # ------------------------------------------------------------------
    # Add channel (multi-step: name -> chat_id)
    # ------------------------------------------------------------------
    @app.on_callback_query(filters.regex(r"^chmenu:add$"))
    @owner_only
    async def channel_add_start(client: Client, callback_query: CallbackQuery):
        admin_id = callback_query.from_user.id
        client.state_service.set(admin_id, action="add_channel", step="awaiting_name")
        await callback_query.message.edit_text(
            "➕ <b>Add Channel</b>\n\nSend a short display name for this channel (e.g. <code>VIP</code>).",
            reply_markup=cancel_keyboard(),
        )
        await callback_query.answer()

    @app.on_message(filters.private & filters.text & filters.create(
        lambda _, c, m: _state_matches(c, m, "add_channel", "awaiting_name")
    ))
    @owner_only
    async def channel_add_receive_name(client: Client, message: Message):
        admin_id = message.from_user.id
        name = message.text.strip()
        if not name:
            await message.reply_text("⚠ Name cannot be empty.")
            return

        existing = await client.channel_service.get_by_name(name)
        if existing:
            await message.reply_text("⚠ A channel with that name already exists. Choose another name.")
            return

        client.state_service.update_data(admin_id, name=name)
        client.state_service.set_step(admin_id, "awaiting_chat_id")
        await message.reply_text(
            "Now identify the channel using <b>one</b> of these methods:\n\n"
            "• Forward a message from the channel <b>directly to me</b> (recommended).\n"
            "• Send its numeric Chat ID, e.g. <code>-1001234567890</code>.\n"
            "• Send its public <code>@username</code>."
        )

    @app.on_message(filters.private & filters.create(
        lambda _, c, m: _state_matches(c, m, "add_channel", "awaiting_chat_id")
    ))
    @owner_only
    async def channel_add_receive_chat_id(client: Client, message: Message):
        admin_id = message.from_user.id

        # Best path: forward any message from the target channel directly to this bot.
        forwarded_chat = getattr(message, "forward_from_chat", None)
        if forwarded_chat:
            chat_ref = forwarded_chat.id
        else:
            raw = (message.text or message.caption or "").strip()
            if not raw:
                await message.reply_text(
                    "⚠ Send the channel Chat ID, its @username, or forward a message "
                    "from the channel directly to me."
                )
                return

            # Accept -100123..., @channelusername, or t.me/channelusername.
            if raw.startswith("https://t.me/") or raw.startswith("http://t.me/"):
                raw = "@" + raw.rstrip("/").rsplit("/", 1)[-1]

            if raw.lstrip("-").isdigit():
                chat_ref = int(raw)
            elif raw.startswith("@") and len(raw) > 1:
                chat_ref = raw
            else:
                await message.reply_text(
                    "⚠ Invalid channel reference. Send a numeric ID such as "
                    "<code>-1001234567890</code>, an <code>@username</code>, or forward "
                    "a message from the channel directly to me."
                )
                return

        state = client.state_service.get(admin_id)
        name = state.data.get("name")

        check = await client.telegram_service.verify_bot_access(chat_ref)
        if not check.get("ok"):
            error = check.get("error") or "UNKNOWN_ERROR"
            stage = check.get("stage")
            chat = check.get("chat")

            if stage == "resolve_chat":
                await message.reply_text(
                    "❌ <b>I could not access that channel.</b>\n\n"
                    f"Telegram error: <code>{error}</code>\n\n"
                    "Check that the Chat ID is correct. The safest method is to "
                    "<b>forward a message from the channel directly to this bot</b>, "
                    "or send the public <code>@channelusername</code>."
                )
            else:
                title = (chat or {}).get("title", "the channel")
                status = check.get("status", "unknown")
                await message.reply_text(
                    f"❌ I found <b>{title}</b>, but this bot is not detected as an administrator.\n\n"
                    f"Bot status: <code>{status}</code>\n"
                    f"Telegram error: <code>{error}</code>\n\n"
                    "Open Channel → Administrators and make sure you added "
                    "<b>this exact bot account</b>, then try again."
                )
            return

        chat_info = check["chat"]
        chat_id = chat_info["id"]

        # Create invite link only after access/admin validation. Failure to create
        # a link should not be confused with inability to see the channel.
        invite_link = await client.telegram_service.create_single_use_invite_link(
            chat_id, name=f"setup-{name}"
        )

        await client.channel_service.add_channel(
            name=name, chat_id=chat_id, invite_link=invite_link or "", enabled=True
        )
        await client.excel_service.ensure_channel_sheet(name)
        await client.excel_service.write_log(
            action="ADD_CHANNEL", admin=str(admin_id), user="-", channel=name, status="ok",
        )

        client.state_service.clear(admin_id)

        permission_notes = []
        if not check.get("can_invite_users", False):
            permission_notes.append("⚠ Grant <b>Invite Users</b> if you want the bot to create invite links.")
        if not check.get("can_restrict_members", False):
            permission_notes.append("⚠ Grant <b>Ban Users / Restrict Members</b> for remove/ban functions.")
        if not invite_link:
            permission_notes.append("⚠ Telegram did not allow creation of an invite link; the channel was still saved.")

        extra = ("\n\n" + "\n".join(permission_notes)) if permission_notes else ""
        await message.reply_text(
            f"✅ Channel <b>{name}</b> added successfully.\n"
            f"Telegram title: <b>{chat_info['title']}</b>\n"
            f"Chat ID: <code>{chat_id}</code>\n"
            f"Bot status: <code>{check.get('status', 'administrator')}</code>"
            f"{extra}",
            reply_markup=back_to_menu_keyboard(),
        )

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
    @app.on_callback_query(filters.regex(r"^chmenu:refresh$"))
    @owner_only
    async def channel_refresh(client: Client, callback_query: CallbackQuery):
        await callback_query.message.edit_text("🔄 Refreshing channels...")
        channels = await client.channel_service.get_all()

        lines = []
        for channel in channels:
            info = await client.telegram_service.get_chat_info(channel["chat_id"])
            if info:
                lines.append(f"✅ {channel['name']} → reachable ({info['title']})")
            else:
                lines.append(f"⚠ {channel['name']} → unreachable (check bot admin rights / chat ID)")

        await client.excel_service.write_log(
            action="REFRESH_CHANNELS", admin=str(callback_query.from_user.id),
            user="-", channel="ALL", status="ok",
        )

        text = "🔄 <b>Refresh Result</b>\n\n" + ("\n".join(lines) if lines else "No channels configured.")
        await callback_query.message.edit_text(text, reply_markup=channel_management_keyboard(channels))
        await callback_query.answer()


def _state_matches(client: Client, message: Message, action: str, step: str) -> bool:
    if not hasattr(client, "state_service") or not message.from_user:
        return False
    state = client.state_service.get(message.from_user.id)
    return bool(state and state.action == action and state.step == step)
