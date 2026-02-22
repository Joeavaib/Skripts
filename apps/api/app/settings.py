from __future__ import annotations

from dataclasses import dataclass
import os
from functools import lru_cache


def _parse_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip().lower() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    """Runtime settings used by deterministic thread extraction."""

    internal_domain_allowlist: tuple[str, ...] = ()
    vip_list: tuple[str, ...] = ()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        internal_domain_allowlist=_parse_csv(os.getenv("INTERNAL_DOMAIN_ALLOWLIST")),
        vip_list=_parse_csv(os.getenv("VIP_LIST")),
    )
