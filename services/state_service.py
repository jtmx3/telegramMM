"""
services/state_service.py
Lightweight in-memory finite-state tracker for multi-step admin flows
(e.g. "waiting for a username after Add Member was pressed").

An instance of StateService is attached to the Pyrogram Client at
startup (app.state_service) and injected into handlers - this keeps
state out of module-level global variables while still being reachable
from every handler.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PendingAction:
    action: str                     # e.g. "add_member", "remove_member", "add_channel"
    step: str                       # e.g. "awaiting_identifier"
    data: dict[str, Any] = field(default_factory=dict)


class StateService:
    def __init__(self):
        self._states: dict[int, PendingAction] = {}

    def set(self, admin_id: int, action: str, step: str, **data) -> None:
        self._states[admin_id] = PendingAction(action=action, step=step, data=data)

    def get(self, admin_id: int) -> Optional[PendingAction]:
        return self._states.get(admin_id)

    def update_data(self, admin_id: int, **data) -> None:
        state = self._states.get(admin_id)
        if state:
            state.data.update(data)

    def set_step(self, admin_id: int, step: str) -> None:
        state = self._states.get(admin_id)
        if state:
            state.step = step

    def clear(self, admin_id: int) -> None:
        self._states.pop(admin_id, None)

    def is_waiting(self, admin_id: int) -> bool:
        return admin_id in self._states
