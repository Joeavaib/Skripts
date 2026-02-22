"""Mailbox sync and processing-queue drain tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

try:
    from sqlalchemy import text
except Exception:  # pragma: no cover
    def text(query: str) -> str:
        return query


from .celery_app import celery_app
from .locks import user_lock
from .tasks_plan import drain_plan_queue


class TransientSyncError(RuntimeError):
    """Recoverable error while syncing mailbox data."""


@dataclass(frozen=True)
class RetryPolicy:
    base_seconds: int = 5
    max_seconds: int = 300

    def countdown(self, retries: int) -> int:
        return min(self.max_seconds, self.base_seconds * (2 ** retries))


RETRY_POLICY = RetryPolicy()


def _claim_next_conversation(session, user_id: int) -> int | None:
    row = session.execute(
        text(
            """
            WITH candidate AS (
                SELECT id
                FROM processing_queue
                WHERE user_id = :user_id
                  AND status = 'queued'
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE processing_queue q
            SET status = 'processing',
                started_at = NOW()
            FROM candidate
            WHERE q.id = candidate.id
            RETURNING q.id, q.conversation_id
            """
        ),
        {"user_id": user_id},
    ).first()
    if not row:
        return None
    return int(row.conversation_id)


def _mark_done(session, user_id: int, conversation_id: int) -> None:
    session.execute(
        text(
            """
            UPDATE processing_queue
            SET status = 'done',
                finished_at = NOW()
            WHERE user_id = :user_id
              AND conversation_id = :conversation_id
              AND status = 'processing'
            """
        ),
        {"user_id": user_id, "conversation_id": conversation_id},
    )


def _perform_sync(session, user_id: int, conversation_id: int) -> None:
    """Hook for real mailbox sync implementation."""

    session.execute(
        text(
            """
            UPDATE mailbox_conversations
            SET last_synced_at = NOW(),
                needs_sync = FALSE
            WHERE user_id = :user_id
              AND id = :conversation_id
            """
        ),
        {"user_id": user_id, "conversation_id": conversation_id},
    )


@celery_app.task(bind=True, name="workers.tasks.sync_mailbox", max_retries=8)
def sync_mailbox(
    self,
    user_id: int,
    *,
    session_factory: Callable[[], object],
) -> bool:
    """Sync one queued conversation for a user using SKIP LOCKED semantics."""

    session = session_factory()
    try:
        with user_lock(session, user_id, namespace="sync-mailbox") as acquired:
            if not acquired:
                return False

            conversation_id = _claim_next_conversation(session, user_id)
            if conversation_id is None:
                session.commit()
                return False

            try:
                _perform_sync(session, user_id, conversation_id)
                _mark_done(session, user_id, conversation_id)
                session.commit()
                return True
            except TransientSyncError as exc:
                session.rollback()
                retries = int(getattr(getattr(self, "request", None), "retries", 0))
                countdown = RETRY_POLICY.countdown(retries)
                raise self.retry(exc=exc, countdown=countdown)
    finally:
        session.close()


@celery_app.task(name="workers.tasks.drain_processing_queue")
def drain_processing_queue(
    user_id: int,
    *,
    session_factory: Callable[[], object],
) -> int:
    """Drain all queued sync work and then kick off plan-drain for same user."""

    processed = 0
    while True:
        handled = sync_mailbox.run(user_id=user_id, session_factory=session_factory)
        if not handled:
            break
        processed += 1

    drain_plan_queue.delay(user_id)
    return processed
