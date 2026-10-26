"""
keyboards/channel_keyboards.py
Builds keyboards that are dynamically generated from channels.json.
Never hardcodes channel names.
"""

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.i18n import TRANSLATIONS


def channel_action_keyboard(channels: list[dict], action_prefix: str, include_all: bool = True, language: str = "en") -> InlineKeyboardMarkup:
    """
    action_prefix examples: 'add', 'remove', 'unban'
    Produces callback_data like 'add_ch:VIP' and, if include_all, 'add_ch:__ALL__'.
    """
    rows = []
    row = []
    for channel in channels:
        name = channel["name"]
        row.append(InlineKeyboardButton(name, callback_data=f"{action_prefix}_ch:{name}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    if include_all and channels:
        label = {
            "en": {"add": "➕ Add To All", "remove": "🗑 Remove From All", "unban": "♻ Unban From All"},
            "ar": {"add": "➕ إضافة إلى الكل", "remove": "🗑 إزالة من الكل", "unban": "♻ فك الحظر من الكل"},
        }.get(language, {}).get(action_prefix, "Apply To All")
        rows.append([InlineKeyboardButton(label, callback_data=f"{action_prefix}_ch:__ALL__")])

    rows.append([InlineKeyboardButton(TRANSLATIONS.get(language, TRANSLATIONS["en"])["cancel"], callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def channel_management_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for channel in channels:
        status_icon = "🟢" if channel.get("enabled", True) else "🔴"
        rows.append([
            InlineKeyboardButton(f"{status_icon} {channel['name']}", callback_data=f"chinfo:{channel['name']}")
        ])

    rows.append([
        InlineKeyboardButton("➕ Add Channel", callback_data="chmenu:add"),
        InlineKeyboardButton("🗑 Delete Channel", callback_data="chmenu:delete"),
    ])
    rows.append([
        InlineKeyboardButton("🔄 Refresh Channels", callback_data="chmenu:refresh"),
    ])
    rows.append([InlineKeyboardButton("« Back to Menu", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def channel_detail_keyboard(channel_name: str, enabled: bool) -> InlineKeyboardMarkup:
    toggle_label = "🔴 Disable" if enabled else "🟢 Enable"
    toggle_action = "disable" if enabled else "enable"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_label, callback_data=f"chtoggle:{toggle_action}:{channel_name}")],
        [InlineKeyboardButton("🗑 Delete This Channel", callback_data=f"chdelete:{channel_name}")],
        [InlineKeyboardButton("« Back to Channels", callback_data="menu:channels")],
    ])


def search_result_keyboard(matches: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for match in matches:
        rows.append([
            InlineKeyboardButton(
                f"{match['channel']} ({match['status']})",
                callback_data=f"noop:{match['channel']}",
            )
        ])
    rows.append([InlineKeyboardButton("« Back to Menu", callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def delete_channel_select_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(c["name"], callback_data=f"chdelete:{c['name']}")] for c in channels]
    rows.append([InlineKeyboardButton("« Back", callback_data="menu:channels")])
    return InlineKeyboardMarkup(rows)
