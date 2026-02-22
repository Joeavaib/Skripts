from __future__ import annotations

import pytest

from apps.api.app.threads.service import (
    PayloadValidationError,
    load_action_card,
    load_thread_pass,
)


def _valid_action_card() -> dict:
    return {
        "schema_version": "action_card.v1",
        "id": "ac-1",
        "title": "Investigate production error",
        "status": "open",
        "priority": "high",
        "owner": "alice",
        "created_at": "2026-01-01T10:00:00Z",
    }


def _valid_thread_pass() -> dict:
    return {
        "schema_version": "thread_pass.v1",
        "thread_id": "thread-1",
        "source_agent": "agent-a",
        "target_agent": "agent-b",
        "handoff_summary": "Continue triage and close open tasks",
        "action_cards": [_valid_action_card()],
        "timeline": [
            {
                "schema_version": "timeline_event.v1",
                "event_id": "evt-1",
                "timestamp": "2026-01-01T10:10:00Z",
                "type": "handoff",
                "message": "Hand-off to agent-b",
            }
        ],
    }


def test_valid_action_card_is_accepted() -> None:
    payload = _valid_action_card()
    assert load_action_card(payload) == payload


def test_action_card_unknown_field_is_rejected() -> None:
    payload = _valid_action_card()
    payload["unknown"] = "nope"

    with pytest.raises(PayloadValidationError):
        load_action_card(payload)


def test_action_card_missing_required_is_rejected() -> None:
    payload = _valid_action_card()
    payload.pop("title")

    with pytest.raises(PayloadValidationError):
        load_action_card(payload)


def test_valid_thread_pass_is_accepted() -> None:
    payload = _valid_thread_pass()
    assert load_thread_pass(payload) == payload


def test_thread_pass_unknown_field_is_rejected() -> None:
    payload = _valid_thread_pass()
    payload["extra"] = True

    with pytest.raises(PayloadValidationError):
        load_thread_pass(payload)


def test_thread_pass_missing_required_is_rejected() -> None:
    payload = _valid_thread_pass()
    payload.pop("thread_id")

    with pytest.raises(PayloadValidationError):
        load_thread_pass(payload)


def test_thread_pass_version_mismatch_is_rejected() -> None:
    payload = _valid_thread_pass()
    payload["schema_version"] = "thread_pass.v2"

    with pytest.raises(PayloadValidationError):
        load_thread_pass(payload)
