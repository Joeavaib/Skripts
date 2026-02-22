from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from .delta import DeltaLinkStore, JsonDict, fetch_delta_pages
from .retry import RetryConfig, send_with_retry


@dataclass(frozen=True)
class GraphClientConfig:
    base_url: str = "https://graph.microsoft.com/v1.0"
    timeout: float = 30.0
    retry: RetryConfig = RetryConfig()


class GraphClient:
    """Minimal Microsoft Graph client with retry and delta helpers."""

    def __init__(
        self,
        token: str,
        *,
        config: GraphClientConfig | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.config = config or GraphClientConfig()
        self._owned_client = client is None
        self._client = client or httpx.Client(timeout=self.config.timeout)
        self._token = token

    def close(self) -> None:
        if self._owned_client:
            self._client.close()

    def __enter__(self) -> "GraphClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _make_url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        return f"{self.config.base_url.rstrip('/')}/{path_or_url.lstrip('/')}"

    def _build_request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[JsonDict] = None,
    ) -> httpx.Request:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        if json is not None:
            headers["Content-Type"] = "application/json"

        return self._client.build_request(
            method,
            self._make_url(path_or_url),
            headers=headers,
            params=params,
            json=json,
        )

    def request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[JsonDict] = None,
    ) -> httpx.Response:
        req = self._build_request(method, path_or_url, params=params, json=json)
        response = send_with_retry(self._client, req, config=self.config.retry)
        response.raise_for_status()
        return response

    def get(self, path_or_url: str, *, params: Optional[dict[str, Any]] = None) -> JsonDict:
        return self.request("GET", path_or_url, params=params).json()

    def post(self, path_or_url: str, *, json: JsonDict) -> JsonDict:
        return self.request("POST", path_or_url, json=json).json()

    def patch(self, path_or_url: str, *, json: JsonDict) -> JsonDict:
        return self.request("PATCH", path_or_url, json=json).json()

    def delete(self, path_or_url: str) -> None:
        self.request("DELETE", path_or_url)

    def delta(self, path_or_url: str, *, store: DeltaLinkStore | None = None) -> list[JsonDict]:
        return fetch_delta_pages(
            self._client,
            base_delta_url=self._make_url(path_or_url),
            store=store,
        )
