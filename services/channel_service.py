"""
services/channel_service.py
Owns channels.json — the dynamic list of channels the bot manages.
No channel is ever hardcoded; everything is loaded from this file at runtime.
"""

import asyncio
import json
from typing import Optional

from config import CHANNELS_FILE
from services.log_service import LogService


class ChannelService:
    def __init__(self, log_service: LogService):
        self._log_service = log_service
        self._lock = asyncio.Lock()
        self._ensure_file()

    # ------------------------------------------------------------------
    def _ensure_file(self) -> None:
        if not CHANNELS_FILE.exists():
            CHANNELS_FILE.parent.mkdir(parents=True, exist_ok=True)
            CHANNELS_FILE.write_text("[]", encoding="utf-8")
            self._log_service.info(f"Created new channels.json at {CHANNELS_FILE}")

    def _read(self) -> list[dict]:
        try:
            raw = CHANNELS_FILE.read_text(encoding="utf-8").strip()
            return json.loads(raw) if raw else []
        except (json.JSONDecodeError, FileNotFoundError):
            self._log_service.error("channels.json was missing or corrupt - resetting to empty list")
            CHANNELS_FILE.write_text("[]", encoding="utf-8")
            return []

    def _write(self, channels: list[dict]) -> None:
        CHANNELS_FILE.write_text(json.dumps(channels, indent=4, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def get_all(self) -> list[dict]:
        async with self._lock:
            return self._read()

    async def get_enabled(self) -> list[dict]:
        async with self._lock:
            return [c for c in self._read() if c.get("enabled", True)]

    async def get_by_name(self, name: str) -> Optional[dict]:
        async with self._lock:
            for c in self._read():
                if c.get("name") == name:
                    return c
            return None

    async def add_channel(self, name: str, chat_id: int, invite_link: str = "", enabled: bool = True) -> bool:
        async with self._lock:
            channels = self._read()
            if any(c.get("name") == name for c in channels):
                return False
            channels.append({
                "name": name,
                "chat_id": chat_id,
                "invite_link": invite_link,
                "enabled": enabled,
            })
            self._write(channels)
            return True

    async def delete_channel(self, name: str) -> bool:
        async with self._lock:
            channels = self._read()
            new_channels = [c for c in channels if c.get("name") != name]
            if len(new_channels) == len(channels):
                return False
            self._write(new_channels)
            return True

    async def set_enabled(self, name: str, enabled: bool) -> bool:
        async with self._lock:
            channels = self._read()
            found = False
            for c in channels:
                if c.get("name") == name:
                    c["enabled"] = enabled
                    found = True
                    break
            if found:
                self._write(channels)
            return found

    async def update_invite_link(self, name: str, invite_link: str) -> bool:
        async with self._lock:
            channels = self._read()
            found = False
            for c in channels:
                if c.get("name") == name:
                    c["invite_link"] = invite_link
                    found = True
                    break
            if found:
                self._write(channels)
            return found
