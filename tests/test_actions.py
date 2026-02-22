import pytest

from apps.api.app.actions.executor import executor
from apps.api.app.actions.routes import (
    ActionRequest,
    UndoRequest,
    execute_action,
    undo_action,
)


@pytest.fixture(autouse=True)
def clear_executor() -> None:
    executor.records.clear()
    executor.action_log.clear()


def test_execute_without_confirm_is_denied() -> None:
    response = execute_action(
        ActionRequest(
            action="move",
            target_id="mail-1",
            payload={"folder": "archive"},
            confirm=False,
        )
    )

    assert response == {"allowed": False, "reason": "confirm_required"}
    assert executor.action_log == []


def test_execute_with_confirm_is_allowed() -> None:
    response = execute_action(
        ActionRequest(
            action="move",
            target_id="mail-1",
            payload={"folder": "archive"},
            confirm=True,
        )
    )

    assert response["allowed"] is True
    assert response["reason"] == "allowed"
    assert response["action_log"]["prev_state_jsonb"]["folder"] == "inbox"
    assert response["action_log"]["new_state_jsonb"]["folder"] == "archive"


@pytest.mark.parametrize(
    ("action", "payload", "assertion_key", "before", "after"),
    [
        ("move", {"folder": "archive"}, "folder", "inbox", "archive"),
        ("categories", {"categories": ["finance", "urgent"]}, "categories", [], ["finance", "urgent"]),
        ("flag", {"flagged": True}, "flagged", False, True),
    ],
)
def test_undo_reverts_reversible_actions(
    action: str,
    payload: dict,
    assertion_key: str,
    before,
    after,
) -> None:
    execute_response = execute_action(
        ActionRequest(
            action=action,
            target_id="mail-undo",
            payload=payload,
            confirm=True,
        )
    )
    action_log_id = execute_response["action_log"]["id"]

    assert execute_response["action_log"]["prev_state_jsonb"][assertion_key] == before
    assert execute_response["action_log"]["new_state_jsonb"][assertion_key] == after

    undo_response = undo_action(UndoRequest(action_log_id=action_log_id))
    assert undo_response["ok"] is True

    record = executor.records["mail-undo"]
    assert record[assertion_key] == before
