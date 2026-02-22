"""Retry-Strategien fuer HTTP-Aufrufe."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import random
import time
from typing import Callable

import httpx


@dataclass(frozen=True)
class RetryConfig:
    """Konfiguration fuer jittered exponential backoff."""

    max_retries: int = 5
    base_delay: float = 0.5
    max_delay: float = 30.0
    jitter_factor: float = 0.2
    retriable_status_codes: tuple[int, ...] = (429, 503)


class MaxRetriesExceeded(RuntimeError):
    """Wird geworfen, wenn alle Retry-Versuche aufgebraucht sind."""



def _parse_retry_after(value: str | None, now: datetime | None = None) -> float | None:
    """Parst den Retry-After Header (Sekunden oder HTTP-Date)."""

    if not value:
        return None

    value = value.strip()
    if not value:
        return None

    if value.isdigit():
        return max(0.0, float(value))

    now = now or datetime.now(timezone.utc)
    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None

    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)

    return max(0.0, (retry_at - now).total_seconds())



def _compute_backoff_delay(attempt: int, config: RetryConfig) -> float:
    """Berechnet jittered exponential backoff fuer den gegebenen Versuch."""

    unclamped = config.base_delay * (2 ** max(0, attempt - 1))
    delay = min(config.max_delay, unclamped)
    jitter_span = max(0.0, delay * config.jitter_factor)
    if jitter_span == 0.0:
        return delay
    return delay + random.uniform(-jitter_span, jitter_span)



def _wait_time(attempt: int, response: httpx.Response | None, config: RetryConfig) -> float:
    """Bestimmt die Wartezeit unter Beruecksichtigung von Retry-After."""

    retry_after = _parse_retry_after(response.headers.get("Retry-After") if response else None)
    if retry_after is not None:
        return min(config.max_delay, retry_after)
    return _compute_backoff_delay(attempt, config)



def request_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    retry_config: RetryConfig | None = None,
    sleep_func: Callable[[float], None] = time.sleep,
    **kwargs,
) -> httpx.Response:
    """Fuehrt einen Request mit Retry auf 429/503 aus."""

    config = retry_config or RetryConfig()
    last_response: httpx.Response | None = None

    for attempt in range(1, config.max_retries + 2):
        response = client.request(method, url, **kwargs)
        last_response = response

        if response.status_code not in config.retriable_status_codes:
            return response

        if attempt > config.max_retries:
            break

        sleep_func(_wait_time(attempt, response, config))

    status = last_response.status_code if last_response is not None else "unknown"
    raise MaxRetriesExceeded(f"Max retries exceeded for {method} {url}; last status={status}")


__all__ = [
    "MaxRetriesExceeded",
    "RetryConfig",
    "request_with_retry",
]
