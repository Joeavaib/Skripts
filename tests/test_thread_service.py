from __future__ import annotations

import unittest

from apps.api.app.threads.service import persist_planner_outputs
from packages.schemas.validator import SchemaValidationError


class FakeRepository:
    def __init__(self) -> None:
        self.saved = False

    def save_planner_outputs(self, **_: object) -> None:
        self.saved = True


def valid_bundle() -> dict[str, object]:
    return {
        "thread_pass": {
            "thread_id": "t_1",
            "pass_id": "p_1",
            "pass_index": 0,
            "created_at": "2025-01-01T00:00:00Z",
            "planner_summary": "all good",
            "action_card_ids": ["ac_1"],
            "timeline_event_ids": ["e_1"],
            "skill_registry_id": "sr_1",
        },
        "action_cards": [
            {
                "card_id": "ac_1",
                "title": "Do thing",
                "kind": "task",
                "status": "todo",
                "priority": 1,
                "created_at": "2025-01-01T00:00:00Z",
            }
        ],
        "skill_registry": {
            "registry_id": "sr_1",
            "generated_at": "2025-01-01T00:00:00Z",
            "skills": [
                {"name": "skill-a", "version": "1.0.0", "enabled": True}
            ],
        },
        "timeline_events": [
            {
                "event_id": "e_1",
                "event_type": "planner_saved",
                "occurred_at": "2025-01-01T00:00:00Z",
                "message": "saved",
            }
        ],
    }


class ThreadServiceTests(unittest.TestCase):
    def test_validation_gate_allows_persist_when_valid(self) -> None:
        repo = FakeRepository()
        bundle = valid_bundle()

        persist_planner_outputs(repo, **bundle)  # type: ignore[arg-type]

        self.assertTrue(repo.saved)

    def test_validation_gate_blocks_persist_when_invalid(self) -> None:
        repo = FakeRepository()
        bundle = valid_bundle()
        bundle["action_cards"] = [
            {
                "card_id": "ac_1",
                "title": "Do thing",
                "kind": "task",
                "status": "todo",
                "priority": 1,
                "created_at": "2025-01-01T00:00:00Z",
                "extra": "disallowed",
            }
        ]

        with self.assertRaises(SchemaValidationError):
            persist_planner_outputs(repo, **bundle)  # type: ignore[arg-type]

        self.assertFalse(repo.saved)


if __name__ == "__main__":
    unittest.main()
