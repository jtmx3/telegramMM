"""Telegram Channel Manager entry point."""

# Must run before importing Pyrogram on Python 3.14+.
from python314_compat import ensure_event_loop
ensure_event_loop()

from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, SESSION_NAME, SESSIONS_DIR, validate_config
from services.log_service import LogService
from services.channel_service import ChannelService
from services.excel_service import ExcelService
from services.state_service import StateService
from services.stats_service import StatsService
from services.telegram_service import TelegramService
from services.i18n import LanguageService
from handlers import (
    start_handler, add_member_handler, remove_member_handler, unban_member_handler,
    search_member_handler, channels_handler, statistics_handler, logs_handler,
    settings_handler, join_handler,
)

def build_app() -> Client:
    missing = validate_config()
    if missing:
        raise RuntimeError("Missing required .env values: " + ", ".join(missing))

    app = Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        workdir=str(SESSIONS_DIR),
    )

    app.log_service = LogService()
    app.channel_service = ChannelService(app.log_service)
    app.excel_service = ExcelService(app.log_service)
    app.state_service = StateService()
    app.language_service = LanguageService()
    app.stats_service = StatsService(app.excel_service)
    app.telegram_service = TelegramService(app, app.log_service)

    for module in (
        start_handler, add_member_handler, remove_member_handler, unban_member_handler,
        search_member_handler, channels_handler, statistics_handler, logs_handler,
        settings_handler, join_handler,
    ):
        module.register(app)
    return app

if __name__ == "__main__":
    application = build_app()
    application.log_service.info(f"Telegram Channel Manager starting for owner {OWNER_ID}")
    application.run()
