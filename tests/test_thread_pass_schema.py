import pytest

from packages.schemas.loader import SchemaValidationError, validate_payload


def _valid_payload() -> dict:
    return {
        "schema_version": "thread_pass.v1",
        "thread_id": "thread-123",
        "handoff_at": "2026-01-01T12:00:00Z",
        "summary": "Kurzüberblick",
        "action_cards": [
            {
                "schema_version": "action_card.v1",
                "id": "ac-1",
                "title": "Klärung offene Frage",
                "status": "open",
                "owner": "team-a",
                "created_at": "2026-01-01T10:00:00Z",
            }
        ],
        "skill_registry": {
            "schema_version": "skill_registry.v1",
            "skills": [
                {"name": "analysis", "version": "1.0.0", "enabled": True}
            ],
        },
        "timeline": [
            {
                "schema_version": "timeline_event.v1",
                "id": "ev-1",
                "timestamp": "2026-01-01T11:00:00Z",
                "actor": "system",
                "type": "note",
                "message": "Übergabe erstellt",
            }
        ],
    }


def test_thread_pass_valid_payload_passes() -> None:
    validate_payload("thread_pass.v1", _valid_payload())


def test_thread_pass_unknown_key_fails() -> None:
    payload = _valid_payload()
    payload["unknown"] = "not-allowed"

    with pytest.raises(SchemaValidationError, match="Additional properties are not allowed"):
        validate_payload("thread_pass.v1", payload)


def test_thread_pass_missing_required_field_fails() -> None:
    payload = _valid_payload()
    del payload["summary"]

    with pytest.raises(SchemaValidationError, match="'summary' is a required property"):
        validate_payload("thread_pass.v1", payload)
