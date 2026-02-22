"""Action execution and undo handling."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ActionLogEntry:
    id: int
    action: str
    target_id: str
    prev_state_jsonb: dict[str, Any]
    new_state_jsonb: dict[str, Any]
    reversible: bool
    created_at: str


@dataclass
class ActionExecutor:
    records: dict[str, dict[str, Any]] = field(default_factory=dict)
    action_log: list[ActionLogEntry] = field(default_factory=list)

    def preview(self, action: str, target_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        before = deepcopy(self._get_or_create(target_id))
        after = deepcopy(before)
        self._apply(action, after, payload)
        return {
            "target_id": target_id,
            "action": action,
            "prev_state_jsonb": before,
            "next_state_jsonb": after,
            "reversible": self._is_reversible(action),
        }

    def execute(self, action: str, target_id: str, payload: dict[str, Any]) -> ActionLogEntry:
        current = self._get_or_create(target_id)
        prev_state = deepcopy(current)
        self._apply(action, current, payload)
        new_state = deepcopy(current)

        entry = ActionLogEntry(
            id=len(self.action_log) + 1,
            action=action,
            target_id=target_id,
            prev_state_jsonb=prev_state,
            new_state_jsonb=new_state,
            reversible=self._is_reversible(action),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.action_log.append(entry)
        return entry

    def undo(self, action_log_id: int) -> ActionLogEntry:
        entry = self._get_log_entry(action_log_id)
        if not entry.reversible:
            raise ValueError("action_not_reversible")

        self.records[entry.target_id] = deepcopy(entry.prev_state_jsonb)

        undo_entry = ActionLogEntry(
            id=len(self.action_log) + 1,
            action=f"undo:{entry.action}",
            target_id=entry.target_id,
            prev_state_jsonb=deepcopy(entry.new_state_jsonb),
            new_state_jsonb=deepcopy(entry.prev_state_jsonb),
            reversible=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.action_log.append(undo_entry)
        return undo_entry

    def _get_or_create(self, target_id: str) -> dict[str, Any]:
        if target_id not in self.records:
            self.records[target_id] = {
                "id": target_id,
                "folder": "inbox",
                "categories": [],
                "flagged": False,
            }
        return self.records[target_id]

    def _get_log_entry(self, action_log_id: int) -> ActionLogEntry:
        for entry in self.action_log:
            if entry.id == action_log_id:
                return entry
        raise ValueError("action_log_not_found")

    @staticmethod
    def _is_reversible(action: str) -> bool:
        return action in {"move", "categories", "flag"}

    @staticmethod
    def _apply(action: str, record: dict[str, Any], payload: dict[str, Any]) -> None:
        if action == "move":
            record["folder"] = payload["folder"]
            return
        if action == "categories":
            record["categories"] = list(payload.get("categories", []))
            return
        if action == "flag":
            record["flagged"] = bool(payload.get("flagged", True))
            return
        raise ValueError("unsupported_action")


executor = ActionExecutor()
