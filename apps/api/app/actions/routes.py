"""Action routes abstraction for preview/execute/undo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.api.app.actions.executor import executor
from packages.policy.gate import evaluate_action_gate


@dataclass
class ActionRequest:
    action: str
    target_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    confirm: bool = False


@dataclass
class UndoRequest:
    action_log_id: int


def preview_action(request: ActionRequest) -> dict[str, Any]:
    decision = evaluate_action_gate(request.action, confirm=request.confirm)
    if not decision.allowed:
        return {"allowed": False, "reason": decision.reason}

    return {
        "allowed": True,
        "reason": decision.reason,
        "preview": executor.preview(request.action, request.target_id, request.payload),
    }


def execute_action(request: ActionRequest) -> dict[str, Any]:
    decision = evaluate_action_gate(request.action, confirm=request.confirm)
    if not decision.allowed:
        return {"allowed": False, "reason": decision.reason}

    entry = executor.execute(request.action, request.target_id, request.payload)
    return {
        "allowed": True,
        "reason": decision.reason,
        "action_log": entry.__dict__,
    }


def undo_action(request: UndoRequest) -> dict[str, Any]:
    entry = executor.undo(request.action_log_id)
    return {
        "ok": True,
        "action_log": entry.__dict__,
    }
