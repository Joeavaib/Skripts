from __future__ import annotations

from typing import Any

from app.actions.executor import execute_action, preview_action, undo_action


def post_preview(action: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    try:
        return 200, {"preview": preview_action(action)}
    except ValueError as exc:
        return 400, {"detail": str(exc)}


def post_execute(req: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    try:
        result = execute_action(req["action"], req.get("confirm", False))
    except PermissionError as exc:
        return 400, {"detail": str(exc)}
    except ValueError as exc:
        return 400, {"detail": str(exc)}

    return 200, {
        "skill_id": result.skill_id,
        "action_type": result.action_type,
        "before": result.before,
        "after": result.after,
        "action_log_id": result.action_log_id,
    }


def post_undo(req: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    try:
        restored = undo_action(req["action_log_id"])
    except LookupError as exc:
        return 404, {"detail": str(exc)}

    return 200, {"restored": restored}
