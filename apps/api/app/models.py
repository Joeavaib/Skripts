from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillState:
    id: str
    category: str | None = None
    folder: str | None = None
    is_draft: bool = True
    is_flagged: bool = False


@dataclass
class ActionLog:
    id: int
    action_type: str
    skill_id: str
    payload_jsonb: dict[str, Any]
    prev_state_jsonb: dict[str, Any]


@dataclass
class InMemoryDB:
    skill_state: dict[str, SkillState] = field(default_factory=dict)
    action_log: list[ActionLog] = field(default_factory=list)
    next_action_log_id: int = 1

    def add_action_log(self, action_type: str, skill_id: str, payload: dict[str, Any], prev_state: dict[str, Any]) -> ActionLog:
        log = ActionLog(
            id=self.next_action_log_id,
            action_type=action_type,
            skill_id=skill_id,
            payload_jsonb=payload,
            prev_state_jsonb=prev_state,
        )
        self.next_action_log_id += 1
        self.action_log.append(log)
        return log


DB = InMemoryDB()


def reset_db() -> None:
    DB.skill_state.clear()
    DB.action_log.clear()
    DB.next_action_log_id = 1
