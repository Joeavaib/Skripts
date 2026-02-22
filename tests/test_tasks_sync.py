from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.workers.app.locks import InMemoryLockStore
from apps.workers.app.tasks_sync import SyncDependencies, sync_mailbox


@dataclass
class FakeBackend:
    changes: list[dict[str, Any]]
    new_cursor: str
    calls: list[tuple[str, str | None]] = field(default_factory=list)

    def pull_changes(self, user_id: str, cursor: str | None) -> tuple[list[dict[str, Any]], str | None]:
        self.calls.append((user_id, cursor))
        return self.changes, self.new_cursor


@dataclass
class FakeMessageStore:
    by_id: dict[str, dict[str, Any]] = field(default_factory=dict)

    def upsert_message(self, message: dict[str, Any]) -> None:
        self.by_id[message["id"]] = message


@dataclass
class FakeQueueStore:
    conversation_ids: set[str] = field(default_factory=set)

    def upsert_conversation(self, conversation_id: str) -> None:
        self.conversation_ids.add(conversation_id)


@dataclass
class FakeSyncState:
    cursors: dict[str, str | None] = field(default_factory=dict)

    def get_cursor(self, user_id: str) -> str | None:
        return self.cursors.get(user_id)

    def set_cursor(self, user_id: str, cursor: str | None) -> None:
        self.cursors[user_id] = cursor


def test_sync_mailbox_upserts_messages_and_processing_queue() -> None:
    backend = FakeBackend(
        changes=[
            {"id": "m1", "conversation_id": "c1", "body": "hello"},
            {"id": "m2", "conversation_id": "c1", "body": "updated"},
            {"id": "m3", "conversation_id": "c2", "body": "world"},
            {"id": "m4", "conversation_id": "c3", "deleted": True},
            {"conversation_id": "missing-id"},
        ],
        new_cursor="cursor-2",
    )
    message_store = FakeMessageStore()
    queue_store = FakeQueueStore()
    sync_state = FakeSyncState(cursors={"user-1": "cursor-1"})

    deps = SyncDependencies(
        backend=backend,
        message_store=message_store,
        processing_queue=queue_store,
        sync_state=sync_state,
        lock_store=InMemoryLockStore(),
    )

    result = sync_mailbox("user-1", deps=deps)

    assert result["status"] == "ok"
    assert result["processed_messages"] == 3
    assert backend.calls == [("user-1", "cursor-1")]
    assert set(message_store.by_id) == {"m1", "m2", "m3"}
    assert queue_store.conversation_ids == {"c1", "c2", "c3"}
    assert sync_state.cursors["user-1"] == "cursor-2"


def test_sync_mailbox_returns_locked_when_lock_exists() -> None:
    lock_store = InMemoryLockStore()
    assert lock_store.acquire("mailbox-sync:user-2") is True

    deps = SyncDependencies(
        backend=FakeBackend(changes=[], new_cursor="cursor-x"),
        message_store=FakeMessageStore(),
        processing_queue=FakeQueueStore(),
        sync_state=FakeSyncState(),
        lock_store=lock_store,
    )

    result = sync_mailbox("user-2", deps=deps)

    assert result == {"status": "locked", "user_id": "user-2"}
