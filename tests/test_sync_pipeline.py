from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from apps.workers.app import tasks_scheduler, tasks_sync


class _Result:
    def __init__(self, *, rows=None, row=None):
        self._rows = rows or []
        self._row = row

    def fetchall(self):
        return self._rows

    def first(self):
        return self._row

    def scalar(self):
        return self._row


class RecordingSession:
    def __init__(self):
        self.sql = []

    def execute(self, stmt, params=None):
        self.sql.append(str(stmt))
        return _Result(row=None)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def test_enqueue_kicks_drain(monkeypatch):
    called = {}

    class Session:
        def execute(self, *_a, **_k):
            return _Result(rows=[(1,), (2,)])

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(
        tasks_scheduler.drain_processing_queue,
        "delay",
        lambda user_id, **kwargs: called.update({"user_id": user_id, **kwargs}),
    )

    inserted = tasks_scheduler.enqueue_sync_jobs.run(11, session_factory=Session, batch_size=100)

    assert inserted == 2
    assert called["user_id"] == 11


def test_drain_processing_queue_runs_until_empty_and_kicks_plan(monkeypatch):
    sequence = iter([True, True, False])
    monkeypatch.setattr(tasks_sync.sync_mailbox, "run", lambda **_: next(sequence))

    kicked = {}
    monkeypatch.setattr(tasks_sync.drain_plan_queue, "delay", lambda user_id: kicked.update(user_id=user_id))

    processed = tasks_sync.drain_processing_queue.run(5, session_factory=lambda: None)

    assert processed == 2
    assert kicked["user_id"] == 5


def test_sync_mailbox_uses_exponential_backoff_for_transient_errors(monkeypatch):
    @contextmanager
    def _lock(*_a, **_k):
        yield True

    monkeypatch.setattr(tasks_sync, "user_lock", _lock)
    monkeypatch.setattr(tasks_sync, "_claim_next_conversation", lambda *_a, **_k: 42)
    monkeypatch.setattr(
        tasks_sync,
        "_perform_sync",
        lambda *_a, **_k: (_ for _ in ()).throw(tasks_sync.TransientSyncError("tmp")),
    )

    captured = {}

    class DummyTask:
        request = SimpleNamespace(retries=2)

        def retry(self, *, exc, countdown):
            captured["exc"] = exc
            captured["countdown"] = countdown
            raise RuntimeError("retried")

    class Session:
        def rollback(self):
            captured["rolled_back"] = True

        def close(self):
            captured["closed"] = True

    with pytest.raises(RuntimeError, match="retried"):
        tasks_sync.sync_mailbox.run(DummyTask(), 1, session_factory=Session)

    assert captured["countdown"] == 20
    assert captured["rolled_back"] is True
    assert captured["closed"] is True


def test_claim_query_contains_skip_locked():
    session = RecordingSession()
    tasks_sync._claim_next_conversation(session, user_id=9)

    assert any("SKIP LOCKED" in sql for sql in session.sql)
