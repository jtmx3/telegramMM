"""
services/log_service.py
Configures application-wide logging (console + rotating file handlers)
and provides a single LogService used to record human-readable events.
"""

import logging
from logging.handlers import RotatingFileHandler

from config import BOT_LOG_FILE, ERROR_LOG_FILE


def _build_logger(name: str, log_file, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        # Already configured (module can be imported multiple times).
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Bot-wide operational logger -> logs/bot.log
bot_logger = _build_logger("bot", BOT_LOG_FILE, logging.INFO)

# Dedicated error logger -> logs/error.log
error_logger = _build_logger("errors", ERROR_LOG_FILE, logging.ERROR)


class LogService:
    """Thin wrapper so handlers/services log consistently without globals."""

    def __init__(self):
        self.bot_logger = bot_logger
        self.error_logger = error_logger

    def info(self, message: str) -> None:
        self.bot_logger.info(message)

    def warning(self, message: str) -> None:
        self.bot_logger.warning(message)

    def error(self, message: str, exc: Exception | None = None) -> None:
        if exc is not None:
            self.error_logger.error("%s | exception=%s", message, repr(exc))
        else:
            self.error_logger.error(message)
