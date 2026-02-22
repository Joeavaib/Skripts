"""Plan-queue related tasks."""

from __future__ import annotations

from .celery_app import celery_app


@celery_app.task(name="workers.tasks.plan.drain")
def drain_plan_queue(user_id: int) -> None:
    """Drain plan queue for a specific user.

    This is intentionally lightweight in this patch; actual plan processing
    can be plugged in by extending this task body.
    """

    _ = user_id
