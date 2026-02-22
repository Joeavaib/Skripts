"""Hilfsfunktionen fuer Graph Delta-Link Verarbeitung."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import httpx


@dataclass(frozen=True)
class DeltaPage:
    items: list[dict]
    next_link: str | None
    delta_link: str | None


@dataclass(frozen=True)
class DeltaResult:
    items: list[dict]
    delta_link: str | None



def parse_delta_page(payload: dict) -> DeltaPage:
    """Extrahiert Werte einer Delta-Seite (`value`, `nextLink`, `deltaLink`)."""

    items = list(payload.get("value") or [])
    next_link = payload.get("@odata.nextLink") or payload.get("nextLink")
    delta_link = payload.get("@odata.deltaLink") or payload.get("deltaLink")
    return DeltaPage(items=items, next_link=next_link, delta_link=delta_link)



def collect_delta(
    start_url: str,
    request_page: Callable[[str], httpx.Response],
) -> DeltaResult:
    """Folgt `nextLink` bis keine weitere Seite vorhanden ist und gibt `deltaLink` zurueck."""

    url = start_url
    all_items: list[dict] = []
    current_delta_link: str | None = None

    while True:
        response = request_page(url)
        response.raise_for_status()
        page = parse_delta_page(response.json())
        all_items.extend(page.items)

        if page.delta_link:
            current_delta_link = page.delta_link

        if not page.next_link:
            break

        url = page.next_link

    return DeltaResult(items=all_items, delta_link=current_delta_link)


__all__ = ["DeltaPage", "DeltaResult", "parse_delta_page", "collect_delta"]
