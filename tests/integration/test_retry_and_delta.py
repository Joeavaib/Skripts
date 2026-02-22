from __future__ import annotations

import httpx
import respx

from packages.graph.delta import DeltaLinkStore, fetch_delta_pages
from packages.graph.retry import RetryConfig, send_with_retry


def test_send_with_retry_honors_retry_after_header() -> None:
    calls: list[float] = []

    with respx.mock(assert_all_called=True) as router:
        route = router.get("https://graph.microsoft.com/v1.0/me")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "3"}),
            httpx.Response(200, json={"ok": True}),
        ]

        web_client = httpx.Client(transport=httpx.HTTPTransport())
        req = web_client.build_request("GET", "https://graph.microsoft.com/v1.0/me")
        response = send_with_retry(
            web_client,
            req,
            config=RetryConfig(max_retries=2, base_delay=0.1, max_delay=1.0),
            sleep_fn=calls.append,
        )

    assert response.status_code == 200
    assert calls == [3.0]


def test_fetch_delta_pages_persists_deltalink(tmp_path) -> None:
    store = DeltaLinkStore(tmp_path / "delta_link.txt")
    base_url = "https://graph.microsoft.com/v1.0/users/delta"

    with respx.mock(assert_all_called=True) as router:
        router.get(base_url).mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [{"id": "1"}],
                    "@odata.nextLink": "https://graph.microsoft.com/v1.0/users/delta?$skiptoken=abc",
                },
            )
        )
        router.get("https://graph.microsoft.com/v1.0/users/delta?$skiptoken=abc").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [{"id": "2"}],
                    "@odata.deltaLink": "https://graph.microsoft.com/v1.0/users/delta?$deltatoken=xyz",
                },
            )
        )

        with httpx.Client() as client:
            pages = fetch_delta_pages(client, base_delta_url=base_url, store=store)

    assert len(pages) == 2
    assert store.load() == "https://graph.microsoft.com/v1.0/users/delta?$deltatoken=xyz"

    with respx.mock(assert_all_called=True) as router:
        router.get("https://graph.microsoft.com/v1.0/users/delta?$deltatoken=xyz").mock(
            return_value=httpx.Response(
                200,
                json={
                    "value": [{"id": "3"}],
                    "@odata.deltaLink": "https://graph.microsoft.com/v1.0/users/delta?$deltatoken=uvw",
                },
            )
        )
        with httpx.Client() as client:
            pages = fetch_delta_pages(client, base_delta_url=base_url, store=store)

    assert len(pages) == 1
    assert pages[0]["value"][0]["id"] == "3"
    assert store.load() == "https://graph.microsoft.com/v1.0/users/delta?$deltatoken=uvw"
