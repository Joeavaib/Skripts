import json

from apps.workers.app.tasks_plan import LOCKED_QUEUE_SELECT, drain_processing_queue
from packages.llm.planner import (
    PlannerSchemaError,
    apply_deterministic_fields,
    persist_cards_to_thread_pass,
    schema_guided_plan,
)


def test_drain_processing_queue_until_empty():
    queue = [
        {"id": 1, "user_id": "u1", "payload": {"x": 1}},
        {"id": 2, "user_id": "u1", "payload": {"x": 2}},
        {"id": 3, "user_id": "u1", "payload": {"x": 3}},
    ]
    seen = []

    def db_fetchall(sql, params):
        assert "FOR UPDATE SKIP LOCKED" in sql
        assert sql == LOCKED_QUEUE_SELECT
        batch = [row for row in queue if row["user_id"] == params["user_id"]][: params["batch_size"]]
        return [dict(row) for row in batch]

    def db_execute(sql, params):
        nonlocal queue
        if sql.startswith("DELETE"):
            queue = [row for row in queue if row["id"] != params["id"]]

    def process_item(row):
        seen.append(row["id"])

    processed = drain_processing_queue(
        "u1",
        db_fetchall=db_fetchall,
        db_execute=db_execute,
        process_item=process_item,
        batch_size=2,
    )

    assert processed == 3
    assert seen == [1, 2, 3]
    assert queue == []


def test_schema_failure_after_retries():
    schema = {
        "type": "object",
        "properties": {"cards": {"type": "array", "items": {"type": "object"}}},
        "required": ["cards"],
        "additionalProperties": False,
    }

    def always_bad(_prompt):
        return '{"not_cards": []}'

    try:
        schema_guided_plan(llm_call=always_bad, user_prompt="plan", schema=schema, max_retries=1)
        assert False, "Expected PlannerSchemaError"
    except PlannerSchemaError as exc:
        assert "failed after retries" in str(exc)


def test_persist_cards_with_deterministic_overrides():
    schema = {
        "type": "object",
        "properties": {
            "cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}},
                    "required": ["title"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["cards"],
        "additionalProperties": False,
    }

    responses = iter([
        "{\"cards\": [{\"title\": \"A\"}]}",
    ])

    result = schema_guided_plan(
        llm_call=lambda _prompt: next(responses),
        user_prompt="make cards",
        schema=schema,
    )

    payload = apply_deterministic_fields(result.payload, thread_id="t-1", run_id="r-1")
    saved = []

    def db_execute(sql, params):
        saved.append((sql, dict(params)))

    count = persist_cards_to_thread_pass(
        db_execute=db_execute,
        thread_id=payload["thread_id"],
        cards=payload["cards"],
    )

    assert payload["thread_id"] == "t-1"
    assert payload["run_id"] == "r-1"
    assert "updated_at" in payload
    assert count == 1
    assert len(saved) == 1
    sql, params = saved[0]
    assert "INSERT INTO thread_pass" in sql
    assert params["thread_id"] == "t-1"
    assert json.loads(params["card_json"]) == {"title": "A"}
