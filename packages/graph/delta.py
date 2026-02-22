from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

import httpx

JsonDict = dict[str, Any]


@dataclass
class DeltaState:
    """Tracks delta traversal links."""

    next_link: Optional[str] = None
    delta_link: Optional[str] = None


class DeltaLinkStore:
    """Simple file-backed deltaLink persistence."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> Optional[str]:
        if not self.path.exists():
            return None
        value = self.path.read_text(encoding="utf-8").strip()
        return value or None

    def save(self, delta_link: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(delta_link, encoding="utf-8")


def extract_links(payload: JsonDict) -> DeltaState:
    """Extract @odata.nextLink and @odata.deltaLink from a delta payload."""
    return DeltaState(
        next_link=payload.get("@odata.nextLink"),
        delta_link=payload.get("@odata.deltaLink"),
    )


def iterate_delta_pages(
    fetch_page: Callable[[str], JsonDict],
    *,
    start_url: str,
    store: DeltaLinkStore | None = None,
) -> Iterator[JsonDict]:
    """Iterate all delta pages from nextLink chain and persist final deltaLink."""
    cursor = start_url
    final_delta_link: Optional[str] = None

    while cursor:
        payload = fetch_page(cursor)
        yield payload

        links = extract_links(payload)
        if links.delta_link:
            final_delta_link = links.delta_link
        cursor = links.next_link

    if final_delta_link and store:
        store.save(final_delta_link)


def build_delta_start_url(base_delta_url: str, store: DeltaLinkStore | None = None) -> str:
    """Use persisted deltaLink if available, otherwise fall back to base delta URL."""
    if store:
        persisted = store.load()
        if persisted:
            return persisted
    return base_delta_url


def fetch_delta_pages(
    client: httpx.Client,
    *,
    base_delta_url: str,
    store: DeltaLinkStore | None = None,
) -> list[JsonDict]:
    """Fetch all delta pages handling nextLink/deltaLink and persistence."""

    def fetch(url: str) -> JsonDict:
        response = client.get(url)
        response.raise_for_status()
        return response.json()

    start_url = build_delta_start_url(base_delta_url, store)
    return list(iterate_delta_pages(fetch, start_url=start_url, store=store))
