"""Celery beat schedule for recurring synchronization tasks."""

from __future__ import annotations

from celery.schedules import crontab

from .celery_app import celery_app

celery_app.conf.beat_schedule = {
    "sync-mailboxes-every-minute": {
        "task": "workers.sync_all_mailboxes",
        "schedule": crontab(),
    }
}
