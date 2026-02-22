from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


class SchemaValidationError(ValueError):
    """Raised when a payload does not satisfy a schema."""


def _schema_path(schema_name: str) -> Path:
    return Path(__file__).resolve().parent / f"{schema_name}.v1.json"


@lru_cache(maxsize=8)
def _load_schema(schema_name: str) -> dict[str, Any]:
    schema_file = _schema_path(schema_name)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    return json.loads(schema_file.read_text(encoding="utf-8"))


def _is_date_time(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _validate_type(expected: str, value: Any) -> bool:
    mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
    }
    py_type = mapping.get(expected)
    if py_type is None:
        return True
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, py_type)


def _raise(path: str, message: str) -> None:
    raise SchemaValidationError(f"validation failed at {path}: {message}")


def _validate(schema: dict[str, Any], value: Any, path: str = "<root>") -> None:
    expected_type = schema.get("type")
    if expected_type and not _validate_type(expected_type, value):
        _raise(path, f"expected {expected_type}")

    if "enum" in schema and value not in schema["enum"]:
        _raise(path, f"value {value!r} is not in enum")

    if expected_type == "object":
        props = schema.get("properties", {})
        required = schema.get("required", [])
        additional_allowed = schema.get("additionalProperties", True)

        for key in required:
            if key not in value:
                _raise(path, f"missing required property '{key}'")

        if additional_allowed is False:
            for key in value:
                if key not in props:
                    _raise(path, f"unknown property '{key}'")

        for key, prop_schema in props.items():
            if key in value:
                _validate(prop_schema, value[key], f"{path}.{key}")

    if expected_type == "array":
        item_schema = schema.get("items")
        if item_schema is not None:
            for idx, item in enumerate(value):
                _validate(item_schema, item, f"{path}[{idx}]")

    if expected_type == "string":
        min_length = schema.get("minLength")
        if min_length is not None and len(value) < min_length:
            _raise(path, f"string shorter than {min_length}")

        if schema.get("format") == "date-time" and not _is_date_time(value):
            _raise(path, "invalid date-time format")

    if expected_type in {"integer", "number"}:
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and value < minimum:
            _raise(path, f"value less than minimum {minimum}")
        if maximum is not None and value > maximum:
            _raise(path, f"value greater than maximum {maximum}")


def validate_payload(schema_name: str, payload: dict[str, Any]) -> None:
    schema = _load_schema(schema_name)
    _validate(schema, payload)


def validate_planner_bundle(*, thread_pass: dict[str, Any], action_cards: list[dict[str, Any]], skill_registry: dict[str, Any], timeline_events: list[dict[str, Any]]) -> None:
    validate_payload("thread_pass", thread_pass)
    validate_payload("skill_registry", skill_registry)

    for action_card in action_cards:
        validate_payload("action_card", action_card)

    for timeline_event in timeline_events:
        validate_payload("timeline_event", timeline_event)
