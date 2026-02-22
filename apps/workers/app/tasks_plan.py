from __future__ import annotations

from typing import Any, Callable

LOCKED_QUEUE_SELECT = """
SELECT id, user_id, payload
FROM processing_queue
WHERE user_id = :user_id
ORDER BY id
FOR UPDATE SKIP LOCKED
LIMIT :batch_size
""".strip()


DELETE_ITEM_SQL = "DELETE FROM processing_queue WHERE id = :id"


def drain_processing_queue(
    user_id: str,
    *,
    db_fetchall: Callable[[str, dict[str, Any]], list[dict[str, Any]]],
    db_execute: Callable[[str, dict[str, Any]], Any],
    process_item: Callable[[dict[str, Any]], Any],
    batch_size: int = 50,
) -> int:
    """Drain all queue items for a user using FOR UPDATE SKIP LOCKED row locking."""

    processed = 0
    while True:
        rows = db_fetchall(LOCKED_QUEUE_SELECT, {"user_id": user_id, "batch_size": batch_size})
        if not rows:
            break

        for row in rows:
            process_item(row)
            db_execute(DELETE_ITEM_SQL, {"id": row["id"]})
            processed += 1

        if len(rows) < batch_size:
            break

    return processed
