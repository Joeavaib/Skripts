from packages.schemas import validate_payload


def validate_thread_pass(payload: dict) -> None:
    """Validate thread pass payload against v1 schema."""
    validate_payload("thread_pass.v1", payload)
