from __future__ import annotations

import unittest

from packages.schemas.validator import SchemaValidationError, validate_payload


class SchemaValidationTests(unittest.TestCase):
    def test_valid_payloads_pass(self) -> None:
        validate_payload(
            "action_card",
            {
                "card_id": "ac_1",
                "title": "Draft plan",
                "kind": "task",
                "status": "todo",
                "priority": 2,
                "created_at": "2025-01-01T00:00:00Z",
            },
        )

    def test_unknown_property_fails(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_payload(
                "timeline_event",
                {
                    "event_id": "e_1",
                    "event_type": "planner_started",
                    "occurred_at": "2025-01-01T00:00:00Z",
                    "message": "started",
                    "unknown": "nope",
                },
            )

    def test_missing_required_fails(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_payload(
                "thread_pass",
                {
                    "thread_id": "t_1",
                    "pass_id": "p_1",
                    "pass_index": 0,
                    "created_at": "2025-01-01T00:00:00Z",
                    "planner_summary": "summary",
                    "action_card_ids": ["ac_1"],
                    "timeline_event_ids": ["e_1"]
                },
            )


if __name__ == "__main__":
    unittest.main()
