from app.actions.routes import post_execute, post_undo
from app.models import DB, reset_db


def test_execute_without_confirm_fails() -> None:
    reset_db()
    status, body = post_execute(
        {
            "confirm": False,
            "action": {"skill_id": "skill-1", "action_type": "draft", "value": False},
        }
    )

    assert status == 400
    assert "confirm=true is required" in body["detail"]


def test_execute_with_confirm_succeeds() -> None:
    reset_db()
    status, body = post_execute(
        {
            "confirm": True,
            "action": {"skill_id": "skill-1", "action_type": "move", "folder": "archive"},
        }
    )

    assert status == 200
    assert body["after"]["folder"] == "archive"
    assert len(DB.action_log) == 1
    assert DB.action_log[0].prev_state_jsonb["folder"] is None


def test_undo_restores_previous_state() -> None:
    reset_db()

    status1, body1 = post_execute(
        {
            "confirm": True,
            "action": {"skill_id": "skill-2", "action_type": "categories", "category": "ops"},
        }
    )
    assert status1 == 200

    status2, _ = post_execute(
        {
            "confirm": True,
            "action": {"skill_id": "skill-2", "action_type": "categories", "category": "eng"},
        }
    )
    assert status2 == 200

    undo_status, undo_body = post_undo({"action_log_id": body1["action_log_id"]})
    assert undo_status == 200
    assert undo_body["restored"]["category"] is None
