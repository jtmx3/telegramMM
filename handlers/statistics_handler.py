"""
handlers/statistics_handler.py
Displays the Statistics screen.
"""

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from handlers.access_control import owner_only
from keyboards.main_menu import back_to_menu_keyboard


def register(app: Client) -> None:

    @app.on_callback_query(filters.regex(r"^menu:statistics$"))
    @owner_only
    async def statistics_menu(client: Client, callback_query: CallbackQuery):
        report = await client.stats_service.build_report()
        await callback_query.message.edit_text(report, reply_markup=back_to_menu_keyboard())
        await callback_query.answer()
