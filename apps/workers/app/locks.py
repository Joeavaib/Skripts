"""PostgreSQL advisory lock helpers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

try:
    from sqlalchemy import text
except Exception:  # pragma: no cover
    def text(query: str) -> str:
        return query



@contextmanager
def user_lock(session, user_id: int, *, namespace: str) -> Iterator[bool]:
    """Acquire/release a transaction-scoped advisory lock for a user.

    Returns a boolean indicating whether lock acquisition succeeded.
    """

    lock_key = f"{namespace}:{user_id}"
    acquired = bool(
        session.execute(
            text("SELECT pg_try_advisory_lock(hashtextextended(:key, 0))"),
            {"key": lock_key},
        ).scalar()
    )
    try:
        yield acquired
    finally:
        if acquired:
            session.execute(
                text("SELECT pg_advisory_unlock(hashtextextended(:key, 0))"),
                {"key": lock_key},
            )
