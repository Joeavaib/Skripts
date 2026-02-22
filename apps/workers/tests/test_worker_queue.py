from apps.workers.queue import worker_name


def test_worker_name_is_not_empty() -> None:
    assert worker_name()
