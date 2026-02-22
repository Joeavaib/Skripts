import pytest
from apps.api.schemas import CreateTaskPayload


def test_create_task_payload_rejects_out_of_range_priority() -> None:
    with pytest.raises(ValueError):
        CreateTaskPayload(task_name="daily-sync", priority=8)
