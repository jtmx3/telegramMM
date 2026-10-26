"""Small bilingual UI layer for the Telegram bot."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


LANG_FILE = Path(__file__).resolve().parent.parent / "user_languages.json"

TRANSLATIONS = {
    "en": {
        "welcome": "👋 <b>Welcome to {app}</b>\n\nUse the menu below to manage your channels.",
        "language": "🌐 Language",
        "language_title": "🌐 <b>Choose your language</b>",
        "english": "🇬🇧 English",
        "arabic": "🇸🇦 العربية",
        "language_saved": "✅ Language changed to {language}.",
        "add_member": "➕ Add Member", "remove_member": "➖ Remove Member",
        "unban_member": "♻ Unban Member", "search_member": "🔍 Search Member",
        "channels": "📢 Channels", "statistics": "📊 Statistics", "logs": "📄 Logs", "settings": "⚙ Settings",
        "back": "« Back to Menu", "cancel": "✖ Cancel",
        "add_member_prompt": "➕ <b>Add Member</b>\n\nSend the target <b>username</b> (e.g. <code>@john</code>) or <b>Telegram ID</b> (e.g. <code>123456789</code>).",
        "invalid_input": "⚠ Invalid input. Send a username or a numeric Telegram ID.",
        "no_enabled_channels": "⚠ No enabled channels found. Add a channel first.",
        "select_channel": "Select which channel to invite <b>{label}</b> to:",
        "session_expired": "Session expired. Start again from the menu.",
        "channel_missing": "Channel not found or disabled.",
        "generating": "⏳ Generating invite link(s)...",
        "link_ready": "✅ Invite link(s) ready for <b>{label}</b>.",
        "send_links": "Send each link below to the user. Once they join, they will be automatically registered in the database.",
        "failed_link": "⚠ Failed to generate invite link.",
    },
    "ar": {
        "welcome": "👋 <b>مرحباً بك في {app}</b>\n\nاستخدم القائمة أدناه لإدارة قنواتك.",
        "language": "🌐 اللغة", "language_title": "🌐 <b>اختر لغتك</b>",
        "english": "🇬🇧 English", "arabic": "🇸🇦 العربية",
        "language_saved": "✅ تم تغيير اللغة إلى {language}.",
        "add_member": "➕ إضافة عضو", "remove_member": "➖ إزالة عضو", "unban_member": "♻ فك حظر عضو", "search_member": "🔍 البحث عن عضو",
        "channels": "📢 القنوات", "statistics": "📊 الإحصائيات", "logs": "📄 السجلات", "settings": "⚙ الإعدادات",
        "back": "« العودة إلى القائمة", "cancel": "✖ إلغاء",
        "add_member_prompt": "➕ <b>إضافة عضو</b>\n\nأرسل <b>اسم المستخدم</b> (مثل <code>@john</code>) أو <b>معرّف تيليغرام</b> (مثل <code>123456789</code>).",
        "invalid_input": "⚠ الإدخال غير صالح. أرسل اسم مستخدم أو معرّف تيليغرام رقمي.",
        "no_enabled_channels": "⚠ لا توجد قنوات مفعّلة. أضف قناة أولاً.",
        "select_channel": "اختر القناة التي تريد دعوة <b>{label}</b> إليها:",
        "session_expired": "انتهت الجلسة. ابدأ من القائمة من جديد.", "channel_missing": "القناة غير موجودة أو غير مفعّلة.",
        "generating": "⏳ جارٍ إنشاء رابط/روابط الدعوة...", "link_ready": "✅ أصبحت روابط الدعوة جاهزة لـ <b>{label}</b>.",
        "send_links": "أرسل كل رابط أدناه إلى المستخدم. عند انضمامه سيتم تسجيله تلقائياً في قاعدة البيانات.",
        "failed_link": "⚠ فشل إنشاء رابط الدعوة.",
    },
}


class LanguageService:
    def __init__(self, path: Path = LANG_FILE):
        self.path = path
        try:
            self.languages = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except Exception:
            self.languages = {}

    def get(self, user_id: int) -> str:
        return self.languages.get(str(user_id), "en")

    def set(self, user_id: int, language: str) -> None:
        if language not in TRANSLATIONS:
            language = "en"
        self.languages[str(user_id)] = language
        self.path.write_text(json.dumps(self.languages, ensure_ascii=False, indent=2), encoding="utf-8")


def t(client: Any, user_id: int, key: str, **kwargs: Any) -> str:
    language = client.language_service.get(user_id) if hasattr(client, "language_service") else "en"
    return TRANSLATIONS.get(language, TRANSLATIONS["en"]).get(key, key).format(**kwargs)


def lang(client: Any, user_id: int) -> str:
    return client.language_service.get(user_id) if hasattr(client, "language_service") else "en"


def rtl(language: str) -> str:
    return "\u200f" if language == "ar" else ""
