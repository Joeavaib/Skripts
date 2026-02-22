"""Ein einfacher Microsoft Graph Client mit Retry- und Delta-Unterstuetzung."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .delta import DeltaResult, collect_delta
from .retry import RetryConfig, request_with_retry


@dataclass
class GraphClient:
    access_token: str
    base_url: str = "https://graph.microsoft.com/v1.0"
    timeout: float = 30.0
    retry_config: RetryConfig = RetryConfig()

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "GraphClient":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def request(self, method: str, path_or_url: str, **kwargs: Any) -> httpx.Response:
        response = request_with_retry(
            self._client,
            method,
            path_or_url,
            retry_config=self.retry_config,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def get_json(self, path_or_url: str, **kwargs: Any) -> dict:
        return self.request("GET", path_or_url, **kwargs).json()

    def get(self, path_or_url: str, **kwargs: Any) -> dict:
        return self.get_json(path_or_url, **kwargs)

    def post(self, path_or_url: str, **kwargs: Any) -> dict:
        return self.request("POST", path_or_url, **kwargs).json()

    def patch(self, path_or_url: str, **kwargs: Any) -> dict:
        return self.request("PATCH", path_or_url, **kwargs).json()

    def delete(self, path_or_url: str, **kwargs: Any) -> None:
        self.request("DELETE", path_or_url, **kwargs)

    def delta(self, start_path_or_url: str) -> DeltaResult:
        """Liest alle Delta-Seiten und liefert Elemente + finalen deltaLink."""

        return collect_delta(start_path_or_url, lambda url: self.request("GET", url))


__all__ = ["GraphClient"]
