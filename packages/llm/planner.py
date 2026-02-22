from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, MutableMapping


class PlannerError(RuntimeError):
    """Base planner exception."""


class PlannerSchemaError(PlannerError):
    """Raised when model output does not match schema."""


@dataclass(slots=True)
class PlannerResult:
    payload: dict[str, Any]
    attempts: int


def _format_json_schema_prompt(schema: Mapping[str, Any]) -> str:
    return (
        "You must answer using ONLY valid JSON that matches this JSON Schema exactly. "
        "Do not include markdown fences or additional text.\n"
        f"Schema:\n{json.dumps(schema, ensure_ascii=False, sort_keys=True)}"
    )


def _extract_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _validate_type(expected: str, value: Any) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate_against_schema(data: Any, schema: Mapping[str, Any], path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type and not _validate_type(expected_type, data):
        raise PlannerSchemaError(f"{path}: expected type {expected_type}, got {type(data).__name__}")

    if "enum" in schema and data not in schema["enum"]:
        raise PlannerSchemaError(f"{path}: value {data!r} not in enum")

    if expected_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional = schema.get("additionalProperties", True)

        for req in required:
            if req not in data:
                raise PlannerSchemaError(f"{path}: missing required field {req}")

        if additional is False:
            extra = set(data.keys()) - set(properties.keys())
            if extra:
                raise PlannerSchemaError(f"{path}: unexpected fields {sorted(extra)}")

        for key, value in data.items():
            if key in properties:
                validate_against_schema(value, properties[key], f"{path}.{key}")

    if expected_type == "array":
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(data):
                validate_against_schema(item, item_schema, f"{path}[{idx}]")


def schema_guided_plan(
    *,
    llm_call: Callable[[str], str],
    user_prompt: str,
    schema: Mapping[str, Any],
    max_retries: int = 2,
) -> PlannerResult:
    """Generate strict JSON output with repair-retry when schema validation fails."""

    schema_prompt = _format_json_schema_prompt(schema)
    full_prompt = f"{schema_prompt}\n\nTask:\n{user_prompt}"

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 2):
        response_text = llm_call(full_prompt)
        try:
            payload = _extract_json(response_text)
            validate_against_schema(payload, schema)
            return PlannerResult(payload=payload, attempts=attempt)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt > max_retries:
                break
            full_prompt = (
                f"{schema_prompt}\n\nThe previous output was invalid: {exc}. "
                "Repair the output so that it matches the schema exactly and reply with JSON only."
            )

    raise PlannerSchemaError(f"Planner failed after retries: {last_error}")


def apply_deterministic_fields(
    plan_payload: MutableMapping[str, Any],
    *,
    thread_id: str,
    run_id: str,
    now: datetime | None = None,
) -> MutableMapping[str, Any]:
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    plan_payload["thread_id"] = thread_id
    plan_payload["run_id"] = run_id
    plan_payload["updated_at"] = stamp
    return plan_payload


def persist_cards_to_thread_pass(
    *,
    db_execute: Callable[[str, Mapping[str, Any]], Any],
    thread_id: str,
    cards: Iterable[Mapping[str, Any]],
) -> int:
    inserted = 0
    statement = (
        "INSERT INTO thread_pass (thread_id, card_index, card_json) "
        "VALUES (:thread_id, :card_index, :card_json)"
    )
    for index, card in enumerate(cards):
        db_execute(
            statement,
            {
                "thread_id": thread_id,
                "card_index": index,
                "card_json": json.dumps(card, ensure_ascii=False),
            },
        )
        inserted += 1
    return inserted
