"""Mailbox synchronization tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .celery_app import celery_app
from .locks import InMemoryLockStore, LockStore, mailbox_lock


class DeltaBackend:
    def pull_changes(self, user_id: str, cursor: str | None) -> tuple[list[dict[str, Any]], str | None]:
        raise NotImplementedError


class MessageStore:
    def upsert_message(self, message: dict[str, Any]) -> None:
        raise NotImplementedError


class ProcessingQueueStore:
    def upsert_conversation(self, conversation_id: str) -> None:
        raise NotImplementedError


class SyncStateStore:
    def get_cursor(self, user_id: str) -> str | None:
        raise NotImplementedError

    def set_cursor(self, user_id: str, cursor: str | None) -> None:
        raise NotImplementedError


@dataclass
class SyncDependencies:
    backend: DeltaBackend
    message_store: MessageStore
    processing_queue: ProcessingQueueStore
    sync_state: SyncStateStore
    lock_store: LockStore


class _NoopBackend(DeltaBackend):
    def pull_changes(self, user_id: str, cursor: str | None) -> tuple[list[dict[str, Any]], str | None]:
        return [], cursor


class _NoopMessageStore(MessageStore):
    def upsert_message(self, message: dict[str, Any]) -> None:
        return None


class _NoopProcessingQueueStore(ProcessingQueueStore):
    def upsert_conversation(self, conversation_id: str) -> None:
        return None


class _InMemorySyncStateStore(SyncStateStore):
    def __init__(self) -> None:
        self._cursor_by_user: dict[str, str | None] = {}

    def get_cursor(self, user_id: str) -> str | None:
        return self._cursor_by_user.get(user_id)

    def set_cursor(self, user_id: str, cursor: str | None) -> None:
        self._cursor_by_user[user_id] = cursor


DEFAULT_DEPS = SyncDependencies(
    backend=_NoopBackend(),
    message_store=_NoopMessageStore(),
    processing_queue=_NoopProcessingQueueStore(),
    sync_state=_InMemorySyncStateStore(),
    lock_store=InMemoryLockStore(),
)


def _iter_changes(changes: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for change in changes:
        if "id" not in change:
            continue
        yield change


@celery_app.task(name="workers.sync_mailbox")
def sync_mailbox(user_id: str, deps: SyncDependencies | None = None) -> dict[str, Any]:
    """Sync mailbox changes for one user and enqueue affected conversations."""

    active_deps = deps or DEFAULT_DEPS
    with mailbox_lock(active_deps.lock_store, user_id) as acquired:
        if not acquired:
            return {"status": "locked", "user_id": user_id}

        cursor = active_deps.sync_state.get_cursor(user_id)
        changes, new_cursor = active_deps.backend.pull_changes(user_id=user_id, cursor=cursor)

        conversation_ids: set[str] = set()
        upserted_messages = 0

        for change in _iter_changes(changes):
            if change.get("deleted"):
                if change.get("conversation_id"):
                    conversation_ids.add(change["conversation_id"])
                continue

            active_deps.message_store.upsert_message(change)
            upserted_messages += 1

            conversation_id = change.get("conversation_id")
            if conversation_id:
                conversation_ids.add(conversation_id)

        for conversation_id in conversation_ids:
            active_deps.processing_queue.upsert_conversation(conversation_id)

        active_deps.sync_state.set_cursor(user_id, new_cursor)

        return {
            "status": "ok",
            "user_id": user_id,
            "processed_messages": upserted_messages,
            "queued_conversations": len(conversation_ids),
            "cursor": new_cursor,
        }


@celery_app.task(name="workers.sync_all_mailboxes")
def sync_all_mailboxes() -> dict[str, str]:
    """Placeholder orchestration task for periodic beat trigger."""

    return {"status": "scheduled"}
