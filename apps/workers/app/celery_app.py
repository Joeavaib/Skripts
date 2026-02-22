"""Celery application bootstrap for worker tasks."""

from __future__ import annotations

import os
from typing import Any, Callable

try:
    from celery import Celery
except Exception:  # pragma: no cover - fallback for environments without celery
    class Celery:  # type: ignore[override]
        def __init__(self, *_: Any, **__: Any) -> None:
            self.conf = {}

        def task(self, *_: Any, **__: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                setattr(func, "delay", lambda *a, **k: func(*a, **k))
                setattr(func, "apply_async", lambda *a, **k: func(*a, **k))
                setattr(func, "run", func)
                return func

            return _decorator


celery_app = Celery(
    "workers",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)

celery_app.conf.update(
    task_default_queue="workers",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)
