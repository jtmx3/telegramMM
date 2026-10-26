"""Handles /start, navigation, and language selection."""
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from config import APP_NAME
from handlers.access_control import owner_only
from keyboards.main_menu import main_menu_keyboard
from services.i18n import t, lang, TRANSLATIONS


def register(app: Client) -> None:
    @app.on_message(filters.command("start") & filters.private)
    @owner_only
    async def start_command(client: Client, message: Message):
        client.state_service.clear(message.from_user.id)
        language = lang(client, message.from_user.id)
        await message.reply_text(t(client, message.from_user.id, "welcome", app=APP_NAME), reply_markup=main_menu_keyboard(language))

    @app.on_callback_query(filters.regex(r"^menu:main$"))
    @owner_only
    async def back_to_main(client: Client, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        client.state_service.clear(user_id)
        await callback_query.message.edit_text(t(client, user_id, "welcome", app=APP_NAME), reply_markup=main_menu_keyboard(lang(client, user_id)))
        await callback_query.answer()

    @app.on_callback_query(filters.regex(r"^menu:language$"))
    @owner_only
    async def language_menu(client: Client, callback_query: CallbackQuery):
        await callback_query.message.edit_text(
            t(client, callback_query.from_user.id, "language_title"),
            reply_markup=__language_keyboard(),
        )
        await callback_query.answer()

    @app.on_callback_query(filters.regex(r"^language:(en|ar)$"))
    @owner_only
    async def set_language(client: Client, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        selected = callback_query.data.split(":", 1)[1]
        client.language_service.set(user_id, selected)
        language_name = TRANSLATIONS[selected]["arabic" if selected == "ar" else "english"]
        await callback_query.message.edit_text(
            t(client, user_id, "language_saved", language=language_name),
            reply_markup=main_menu_keyboard(selected),
        )
        await callback_query.answer()

    @app.on_callback_query(filters.regex(r"^noop:"))
    @owner_only
    async def noop(client: Client, callback_query: CallbackQuery):
        await callback_query.answer()


def __language_keyboard():
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="language:en")],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="language:ar")],
        [InlineKeyboardButton("« Back", callback_data="menu:main")],
    ])
