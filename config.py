"""Central configuration for Telegram Channel Manager."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
DATABASE_DIR = BASE_DIR / "database"
LOGS_DIR = BASE_DIR / "logs"
IMAGES_DIR = BASE_DIR / "images"
SESSIONS_DIR = BASE_DIR / "sessions"
EXCEL_FILE = DATABASE_DIR / "members.xlsx"
CHANNELS_FILE = BASE_DIR / "channels.json"
BOT_LOG_FILE = LOGS_DIR / "bot.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"

for directory in (DATABASE_DIR, LOGS_DIR, IMAGES_DIR, SESSIONS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

load_dotenv(dotenv_path=ENV_FILE)

def _safe_int(value: str | None, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default

API_ID = _safe_int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID = _safe_int(os.getenv("OWNER_ID"))

PERMISSION_DENIED_MESSAGE = "You don't have permission."
SYSTEM_SHEETS = ("Logs", "Settings")
MEMBER_COLUMNS = ("TelegramID", "Username", "FullName", "JoinDate", "Status")
LOG_COLUMNS = ("Date", "Time", "Action", "Admin", "User", "Channel", "Status")
SESSION_NAME = "channel_manager_bot"
APP_NAME = "Telegram Channel Manager"

def validate_config() -> list[str]:
    missing = []
    if not API_ID: missing.append("API_ID")
    if not API_HASH: missing.append("API_HASH")
    if not BOT_TOKEN: missing.append("BOT_TOKEN")
    if not OWNER_ID: missing.append("OWNER_ID")
    return missing
