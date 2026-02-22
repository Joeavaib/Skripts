from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models import DB, SkillState

SUPPORTED_ACTIONS = {"draft", "categories", "move", "flag"}


@dataclass
class ExecutionResult:
    skill_id: str
    action_type: str
    before: dict[str, Any]
    after: dict[str, Any]
    action_log_id: int


def _state_to_dict(state: SkillState) -> dict[str, Any]:
    return {
        "id": state.id,
        "category": state.category,
        "folder": state.folder,
        "is_draft": state.is_draft,
        "is_flagged": state.is_flagged,
    }


def _ensure_state(skill_id: str) -> SkillState:
    if skill_id not in DB.skill_state:
        DB.skill_state[skill_id] = SkillState(id=skill_id)
    return DB.skill_state[skill_id]


def preview_action(payload: dict[str, Any]) -> dict[str, Any]:
    action_type = payload["action_type"]
    if action_type not in SUPPORTED_ACTIONS:
        raise ValueError(f"Unsupported action_type: {action_type}")

    changes: dict[str, Any] = {}
    if action_type == "draft":
        changes["is_draft"] = bool(payload["value"])
    elif action_type == "categories":
        changes["category"] = payload["category"]
    elif action_type == "move":
        changes["folder"] = payload["folder"]
    elif action_type == "flag":
        changes["is_flagged"] = bool(payload["value"])

    return {"skill_id": payload["skill_id"], "action_type": action_type, "changes": changes}


def execute_action(payload: dict[str, Any], confirm: bool) -> ExecutionResult:
    if not confirm:
        raise PermissionError("confirm=true is required for write actions")

    plan = preview_action(payload)
    state = _ensure_state(plan["skill_id"])
    before = _state_to_dict(state)

    for key, value in plan["changes"].items():
        setattr(state, key, value)

    after = _state_to_dict(state)
    log = DB.add_action_log(plan["action_type"], plan["skill_id"], payload, before)

    return ExecutionResult(
        skill_id=plan["skill_id"],
        action_type=plan["action_type"],
        before=before,
        after=after,
        action_log_id=log.id,
    )


def undo_action(action_log_id: int) -> dict[str, Any]:
    log = next((entry for entry in DB.action_log if entry.id == action_log_id), None)
    if log is None:
        raise LookupError("action log entry not found")

    state = _ensure_state(log.skill_id)
    prev = log.prev_state_jsonb

    state.category = prev.get("category")
    state.folder = prev.get("folder")
    state.is_draft = bool(prev.get("is_draft", True))
    state.is_flagged = bool(prev.get("is_flagged", False))

    return _state_to_dict(state)
