"""Small helpers shared by member-management handlers."""
from typing import Optional

def parse_identifier(text: str | None) -> tuple[Optional[int], Optional[str]]:
    if not text:
        return None, None
    value = text.strip()
    if not value:
        return None, None
    if value.startswith("@"):
        username = value[1:].strip()
        return (None, username) if username else (None, None)
    try:
        return int(value), None
    except ValueError:
        # Accept bare Telegram usernames as a convenience.
        if all(ch.isalnum() or ch == "_" for ch in value):
            return None, value
        return None, None

def format_member_line(member: dict) -> str:
    username = member.get("username")
    label = f"@{username}" if username else str(member.get("telegram_id", "-"))
    full_name = member.get("full_name") or "-"
    status = member.get("status") or "-"
    channel = member.get("channel") or "-"
    return f"• <b>{label}</b> — {full_name}\n  Channel: <b>{channel}</b> | Status: <b>{status}</b>"
