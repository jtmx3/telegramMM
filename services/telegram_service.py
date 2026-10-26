"""Thin, exception-safe wrapper around Pyrogram Telegram operations."""
from typing import Any
from pyrogram import Client
from pyrogram.errors import RPCError
from services.log_service import LogService


class TelegramService:
    def __init__(self, client: Client, log_service: LogService):
        self._client = client
        self._log_service = log_service

    async def ban_member(self, chat_id: int, user_id: int | None) -> tuple[bool, str]:
        if user_id is None:
            return False, "missing_user_id"
        try:
            await self._client.ban_chat_member(chat_id, user_id)
            return True, "banned"
        except RPCError as exc:
            self._log_service.error(f"ban_member failed chat_id={chat_id} user_id={user_id}", exc)
            return False, str(exc)
        except Exception as exc:
            self._log_service.error(f"ban_member unexpected error chat_id={chat_id} user_id={user_id}", exc)
            return False, repr(exc)

    async def unban_member(self, chat_id: int, user_id: int | None) -> tuple[bool, str]:
        if user_id is None:
            return False, "missing_user_id"
        try:
            await self._client.unban_chat_member(chat_id, user_id)
            return True, "unbanned"
        except RPCError as exc:
            self._log_service.error(f"unban_member failed chat_id={chat_id} user_id={user_id}", exc)
            return False, str(exc)
        except Exception as exc:
            self._log_service.error(f"unban_member unexpected error chat_id={chat_id} user_id={user_id}", exc)
            return False, repr(exc)

    async def create_single_use_invite_link(self, chat_id: int, name: str | None = None) -> str | None:
        try:
            invite = await self._client.create_chat_invite_link(chat_id, name=name, member_limit=1)
            return invite.invite_link
        except RPCError as exc:
            self._log_service.error(f"create_single_use_invite_link failed chat_id={chat_id}", exc)
            return None
        except Exception as exc:
            self._log_service.error(f"create_single_use_invite_link unexpected error chat_id={chat_id}", exc)
            return None

    async def get_chat_info(self, chat_ref: int | str) -> dict[str, Any] | None:
        """Return basic chat details for an ID or @username."""
        result = await self.verify_bot_access(chat_ref)
        return result.get("chat") if result.get("ok") else None

    async def verify_bot_access(self, chat_ref: int | str) -> dict[str, Any]:
        """
        Resolve a chat and verify the *actual bot account* is an administrator.

        Returns a diagnostic dictionary instead of collapsing every Telegram RPC
        error into a misleading 'bot is not admin' message.
        """
        try:
            chat = await self._client.get_chat(chat_ref)
        except RPCError as exc:
            self._log_service.error(f"get_chat failed chat_ref={chat_ref}", exc)
            return {
                "ok": False,
                "stage": "resolve_chat",
                "error": str(exc),
                "chat": None,
            }
        except Exception as exc:
            self._log_service.error(f"get_chat unexpected error chat_ref={chat_ref}", exc)
            return {
                "ok": False,
                "stage": "resolve_chat",
                "error": repr(exc),
                "chat": None,
            }

        chat_info = {
            "id": chat.id,
            "title": chat.title or getattr(chat, "first_name", None) or str(chat.id),
            "type": str(chat.type),
            "username": getattr(chat, "username", None),
        }

        try:
            me = await self._client.get_me()
            member = await self._client.get_chat_member(chat.id, me.id)
            status_obj = getattr(member, "status", "")
            status = getattr(status_obj, "value", str(status_obj)).lower()
            is_admin = status in {"administrator", "owner", "creator"} or "administrator" in status or "owner" in status

            privileges = getattr(member, "privileges", None)
            can_invite_users = bool(getattr(privileges, "can_invite_users", False)) if privileges else False
            can_restrict_members = bool(getattr(privileges, "can_restrict_members", False)) if privileges else False

            if not is_admin:
                return {
                    "ok": False,
                    "stage": "admin_check",
                    "error": f"BOT_STATUS_{status or 'unknown'}",
                    "chat": chat_info,
                    "status": status,
                    "can_invite_users": can_invite_users,
                    "can_restrict_members": can_restrict_members,
                }

            return {
                "ok": True,
                "stage": "ok",
                "error": None,
                "chat": chat_info,
                "status": status,
                "can_invite_users": can_invite_users,
                "can_restrict_members": can_restrict_members,
            }
        except RPCError as exc:
            self._log_service.error(f"get_chat_member failed chat_id={chat.id}", exc)
            return {
                "ok": False,
                "stage": "admin_check",
                "error": str(exc),
                "chat": chat_info,
            }
        except Exception as exc:
            self._log_service.error(f"get_chat_member unexpected error chat_id={chat.id}", exc)
            return {
                "ok": False,
                "stage": "admin_check",
                "error": repr(exc),
                "chat": chat_info,
            }

    async def resolve_user(self, identifier) -> dict[str, Any] | None:
        try:
            user = await self._client.get_users(identifier)
            full_name = " ".join(filter(None, [user.first_name, user.last_name]))
            return {"id": user.id, "username": user.username, "full_name": full_name}
        except RPCError as exc:
            self._log_service.error(f"resolve_user failed identifier={identifier}", exc)
            return None
        except Exception as exc:
            self._log_service.error(f"resolve_user unexpected error identifier={identifier}", exc)
            return None

    async def send_message_safe(self, chat_id: int, text: str, **kwargs) -> bool:
        try:
            await self._client.send_message(chat_id, text, **kwargs)
            return True
        except Exception as exc:
            self._log_service.error(f"send_message_safe failed chat_id={chat_id}", exc)
            return False
