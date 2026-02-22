from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SCHEMA_DIR = Path(__file__).resolve().parents[4] / "packages" / "schemas"


class PayloadValidationError(ValueError):
    """Raised when payload validation fails."""


def _normalize_payload(payload: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        parsed = json.loads(payload)
        if isinstance(parsed, dict):
            return parsed
    raise PayloadValidationError("Payload must be a dictionary or JSON object string.")


@lru_cache(maxsize=None)
def _load_schema_file(filename: str) -> dict[str, Any]:
    schema_path = SCHEMA_DIR / filename
    if not schema_path.exists():
        raise PayloadValidationError(f"Schema not found: {filename}")
    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_type(value: Any, expected: str, path: str) -> None:
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "boolean": bool,
    }
    py_type = type_map.get(expected)
    if py_type is None:
        return
    if not isinstance(value, py_type) or (expected == "integer" and isinstance(value, bool)):
        raise PayloadValidationError(f"{path} must be of type {expected}.")


def _validate(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type:
        _validate_type(value, expected_type, path)

    if "const" in schema and value != schema["const"]:
        raise PayloadValidationError(f"{path} must be exactly '{schema['const']}'.")

    if "enum" in schema and value not in schema["enum"]:
        raise PayloadValidationError(f"{path} must be one of {schema['enum']}.")

    if isinstance(value, str) and "minLength" in schema and len(value) < schema["minLength"]:
        raise PayloadValidationError(f"{path} must have min length {schema['minLength']}.")

    if isinstance(value, int) and "minimum" in schema and value < schema["minimum"]:
        raise PayloadValidationError(f"{path} must be >= {schema['minimum']}.")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise PayloadValidationError(f"{path}.{key} is required.")

        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        if additional is False:
            unknown = set(value.keys()) - set(properties.keys())
            if unknown:
                raise PayloadValidationError(f"{path} has unknown field(s): {sorted(unknown)}.")

        for key, field_value in value.items():
            prop_schema = properties.get(key)
            if prop_schema is not None:
                _validate(field_value, prop_schema, f"{path}.{key}")

    if isinstance(value, list):
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(value):
                _validate(item, item_schema, f"{path}[{idx}]")


def _validate_payload(
    payload: dict[str, Any] | str,
    *,
    schema_filename: str,
    expected_version: str,
) -> dict[str, Any]:
    normalized = _normalize_payload(payload)

    schema_version = normalized.get("schema_version")
    if schema_version != expected_version:
        raise PayloadValidationError(
            f"Invalid schema_version '{schema_version}'. Expected '{expected_version}'."
        )

    schema = _load_schema_file(schema_filename)
    _validate(normalized, schema)
    return normalized


def load_thread_pass(payload: dict[str, Any] | str) -> dict[str, Any]:
    return _validate_payload(
        payload,
        schema_filename="thread_pass.v1.json",
        expected_version="thread_pass.v1",
    )


def load_action_card(payload: dict[str, Any] | str) -> dict[str, Any]:
    return _validate_payload(
        payload,
        schema_filename="action_card.v1.json",
        expected_version="action_card.v1",
    )
