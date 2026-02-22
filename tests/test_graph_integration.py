from __future__ import annotations

import httpx
import respx

from packages.graph.client import GraphClient
from packages.graph.retry import RetryConfig


def test_retry_on_429_then_success() -> None:
    with respx.mock(base_url="https://graph.microsoft.com/v1.0") as router:
        route = router.get("/me").mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "0"}),
                httpx.Response(200, json={"id": "abc"}),
            ]
        )

        client = GraphClient(
            access_token="token",
            retry_config=RetryConfig(max_retries=2, base_delay=0.01),
        )
        try:
            # direkte Retry-Funktion injizieren wir ueber request mit sleep patch nicht,
            # daher monkeypatch per kwargs an request_with_retry ist hier nicht vorgesehen.
            # Fuer Integration testen wir den echten Ablauf inkl. Retry-After via kurzer Wartezeit.
            payload = client.get("/me")
        finally:
            client.close()

    assert payload == {"id": "abc"}
    assert route.call_count == 2


def test_delta_pagination_collects_all_items_and_returns_delta_link() -> None:
    with respx.mock(base_url="https://graph.microsoft.com/v1.0") as router:
        router.get("/users/delta").respond(
            200,
            json={
                "value": [{"id": "1"}],
                "@odata.nextLink": "https://graph.microsoft.com/v1.0/users/delta?$skiptoken=abc",
            },
        )
        router.get("/users/delta?$skiptoken=abc").respond(
            200,
            json={
                "value": [{"id": "2"}],
                "@odata.deltaLink": "https://graph.microsoft.com/v1.0/users/delta?$deltatoken=final",
            },
        )

        with GraphClient(access_token="token") as client:
            result = client.delta("/users/delta")

    assert [item["id"] for item in result.items] == ["1", "2"]
    assert result.delta_link == "https://graph.microsoft.com/v1.0/users/delta?$deltatoken=final"


def test_delta_link_persistence_followup_sync() -> None:
    with respx.mock(base_url="https://graph.microsoft.com/v1.0") as router:
        router.get("/groups/delta").respond(
            200,
            json={
                "value": [{"id": "g1"}],
                "@odata.deltaLink": "https://graph.microsoft.com/v1.0/groups/delta?$deltatoken=first",
            },
        )
        router.get("/groups/delta?$deltatoken=first").respond(
            200,
            json={
                "value": [{"id": "g2"}],
                "@odata.deltaLink": "https://graph.microsoft.com/v1.0/groups/delta?$deltatoken=second",
            },
        )

        with GraphClient(access_token="token") as client:
            first_sync = client.delta("/groups/delta")
            second_sync = client.delta(first_sync.delta_link or "")

    assert [item["id"] for item in first_sync.items] == ["g1"]
    assert first_sync.delta_link == "https://graph.microsoft.com/v1.0/groups/delta?$deltatoken=first"
    assert [item["id"] for item in second_sync.items] == ["g2"]
    assert second_sync.delta_link == "https://graph.microsoft.com/v1.0/groups/delta?$deltatoken=second"
