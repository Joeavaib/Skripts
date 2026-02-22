from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

SCHEMA_DIR = Path(__file__).resolve().parent


class SchemaValidationError(ValueError):
    """Raised when a payload does not conform to the requested JSON schema."""


@lru_cache(maxsize=32)
def load_schema(schema_name: str) -> dict[str, Any]:
    schema_path = SCHEMA_DIR / f"{schema_name}.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Unknown schema: {schema_name}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _schema_store() -> dict[str, dict[str, Any]]:
    store: dict[str, dict[str, Any]] = {}
    for path in SCHEMA_DIR.glob("*.v1.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema_id = schema.get("$id")
        if schema_id:
            store[schema_id] = schema
    return store


def _raise(message: str, path: str) -> None:
    if path:
        raise SchemaValidationError(f"{message} at {path}")
    raise SchemaValidationError(message)


def _is_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _validate(schema: dict[str, Any], data: Any, path: str = "") -> None:
    if "$ref" in schema:
        ref_name = schema["$ref"]
        target = _schema_store().get(ref_name)
        if target is None:
            _raise(f"Unknown schema reference '{ref_name}'", path)
        _validate(target, data, path)
        return

    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(data, dict):
            _raise("Expected object", path)

        required = schema.get("required", [])
        for key in required:
            if key not in data:
                _raise(f"'{key}' is a required property", path)

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = [key for key in data if key not in properties]
            if extras:
                _raise("Additional properties are not allowed", path)

        for key, value in data.items():
            if key in properties:
                child_path = f"{path}.{key}" if path else key
                _validate(properties[key], value, child_path)
        return

    if expected_type == "array":
        if not isinstance(data, list):
            _raise("Expected array", path)
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(data):
                child_path = f"{path}[{index}]"
                _validate(item_schema, item, child_path)
        return

    if expected_type == "string":
        if not isinstance(data, str):
            _raise("Expected string", path)
        min_length = schema.get("minLength")
        if min_length is not None and len(data) < min_length:
            _raise(f"String must have at least {min_length} characters", path)
        enum = schema.get("enum")
        if enum and data not in enum:
            _raise(f"Value must be one of {enum}", path)
        const = schema.get("const")
        if const is not None and data != const:
            _raise(f"Value must be '{const}'", path)
        if schema.get("format") == "date-time" and not _is_datetime(data):
            _raise("Value must be a valid date-time", path)
        return

    if expected_type == "boolean":
        if not isinstance(data, bool):
            _raise("Expected boolean", path)
        return


def validate_payload(schema_name: str, payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise SchemaValidationError("Payload must be an object")

    schema_version = payload.get("schema_version")
    if schema_version != schema_name:
        raise SchemaValidationError(
            f"schema_version mismatch: expected '{schema_name}', got '{schema_version}'"
        )

    schema = load_schema(schema_name)
    _validate(schema, payload)
