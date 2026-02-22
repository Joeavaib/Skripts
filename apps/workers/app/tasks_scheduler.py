"""Scheduling tasks that enqueue mailbox sync jobs."""

from __future__ import annotations

from typing import Callable

try:
    from sqlalchemy import text
except Exception:  # pragma: no cover
    def text(query: str) -> str:
        return query


from .celery_app import celery_app
from .tasks_sync import drain_processing_queue


@celery_app.task(name="workers.tasks.enqueue_sync_jobs")
def enqueue_sync_jobs(
    user_id: int,
    *,
    session_factory: Callable[[], object],
    batch_size: int = 200,
) -> int:
    """Enqueue sync jobs from mailbox conversations and kick queue drain."""

    session = session_factory()
    try:
        inserted = session.execute(
            text(
                """
                INSERT INTO processing_queue (user_id, conversation_id, status)
                SELECT c.user_id, c.id, 'queued'
                FROM mailbox_conversations c
                WHERE c.user_id = :user_id
                  AND c.needs_sync = TRUE
                ORDER BY c.updated_at
                LIMIT :batch_size
                ON CONFLICT (user_id, conversation_id) DO NOTHING
                RETURNING conversation_id
                """
            ),
            {"user_id": user_id, "batch_size": batch_size},
        ).fetchall()
        session.commit()

        if inserted:
            drain_processing_queue.delay(user_id, session_factory=session_factory)

        return len(inserted)
    finally:
        session.close()
