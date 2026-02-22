from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import httpx

RETRYABLE_STATUS_CODES = {429, 503}


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 5
    base_delay: float = 0.5
    max_delay: float = 30.0
    jitter_ratio: float = 0.2


def parse_retry_after(value: str | None, *, now: Optional[datetime] = None) -> float | None:
    """Parse an HTTP Retry-After header value.

    Supports either delta-seconds or an HTTP date.
    Returns seconds to wait if parseable and positive, otherwise None.
    """
    if not value:
        return None

    stripped = value.strip()
    if stripped.isdigit():
        return max(float(stripped), 0.0)

    try:
        dt = parsedate_to_datetime(stripped)
    except (TypeError, ValueError):
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now_dt = now if now is not None else datetime.now(timezone.utc)
    delta = (dt - now_dt).total_seconds()
    return max(delta, 0.0)


def compute_backoff_delay(attempt: int, config: RetryConfig, *, rng: random.Random | None = None) -> float:
    """Compute jittered exponential backoff for an attempt (1-based)."""
    rand = rng if rng is not None else random
    exponential = config.base_delay * (2 ** max(attempt - 1, 0))
    capped = min(exponential, config.max_delay)
    jitter = capped * config.jitter_ratio
    low = max(0.0, capped - jitter)
    high = capped + jitter
    return rand.uniform(low, high)


def should_retry(response: httpx.Response) -> bool:
    return response.status_code in RETRYABLE_STATUS_CODES


def send_with_retry(
    client: httpx.Client,
    request: httpx.Request,
    *,
    config: RetryConfig | None = None,
    sleep_fn=time.sleep,
    rng: random.Random | None = None,
) -> httpx.Response:
    """Send a request with retry support for 429/503 responses.

    Honors Retry-After if present; otherwise uses jittered exponential backoff.
    """
    cfg = config or RetryConfig()

    for attempt in range(1, cfg.max_retries + 2):
        response = client.send(request)

        if not should_retry(response):
            return response

        if attempt > cfg.max_retries:
            return response

        retry_after = parse_retry_after(response.headers.get("Retry-After"))
        delay = retry_after if retry_after is not None else compute_backoff_delay(attempt, cfg, rng=rng)
        sleep_fn(delay)

    return response
