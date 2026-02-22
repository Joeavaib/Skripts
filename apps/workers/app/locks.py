"""Locking primitives for mailbox sync tasks."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from typing import Iterator


class LockStore:
    """Interface for acquiring and releasing named locks."""

    def acquire(self, key: str) -> bool:
        raise NotImplementedError

    def release(self, key: str) -> None:
        raise NotImplementedError


@dataclass
class InMemoryLockStore(LockStore):
    """Simple lock store for tests and local execution."""

    _guard: Lock = field(default_factory=Lock)
    _locks: set[str] = field(default_factory=set)

    def acquire(self, key: str) -> bool:
        with self._guard:
            if key in self._locks:
                return False
            self._locks.add(key)
            return True

    def release(self, key: str) -> None:
        with self._guard:
            self._locks.discard(key)


@contextmanager
def mailbox_lock(lock_store: LockStore, user_id: str) -> Iterator[bool]:
    """Context manager acquiring/releasing a mailbox-specific lock."""

    key = f"mailbox-sync:{user_id}"
    acquired = lock_store.acquire(key)
    try:
        yield acquired
    finally:
        if acquired:
            lock_store.release(key)
