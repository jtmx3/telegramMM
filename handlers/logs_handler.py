"""
handlers/logs_handler.py
Displays the most recent entries from the Logs sheet.
"""

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from handlers.access_control import owner_only
from keyboards.main_menu import back_to_menu_keyboard


def register(app: Client) -> None:

    @app.on_callback_query(filters.regex(r"^menu:logs$"))
    @owner_only
    async def logs_menu(client: Client, callback_query: CallbackQuery):
        rows = await client.excel_service.get_recent_logs(limit=15)

        if not rows:
            text = "📄 <b>Logs</b>\n\nNo operations recorded yet."
        else:
            lines = ["📄 <b>Logs</b> (most recent 15)\n"]
            for date, time, action, admin, user, channel, status in rows:
                lines.append(
                    f"🕒 {date} {time} | <b>{action}</b> | admin={admin} | "
                    f"user={user} | ch={channel} | {status}"
                )
            text = "\n".join(lines)

        await callback_query.message.edit_text(text, reply_markup=back_to_menu_keyboard())
        await callback_query.answer()
