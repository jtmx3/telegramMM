"""Localized inline keyboards."""
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.i18n import TRANSLATIONS


def _s(language, key):
    return TRANSLATIONS.get(language, TRANSLATIONS["en"])[key]


def main_menu_keyboard(language="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(_s(language, "add_member"), callback_data="menu:add_member"), InlineKeyboardButton(_s(language, "remove_member"), callback_data="menu:remove_member")],
        [InlineKeyboardButton(_s(language, "unban_member"), callback_data="menu:unban_member"), InlineKeyboardButton(_s(language, "search_member"), callback_data="menu:search_member")],
        [InlineKeyboardButton(_s(language, "channels"), callback_data="menu:channels"), InlineKeyboardButton(_s(language, "statistics"), callback_data="menu:statistics")],
        [InlineKeyboardButton(_s(language, "logs"), callback_data="menu:logs"), InlineKeyboardButton(_s(language, "settings"), callback_data="menu:settings")],
        [InlineKeyboardButton(_s(language, "language"), callback_data="menu:language")],
    ])


def back_to_menu_keyboard(language="en"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(_s(language, "back"), callback_data="menu:main")]])


def cancel_keyboard(language="en"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(_s(language, "cancel"), callback_data="menu:main")]])
