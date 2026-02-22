from __future__ import annotations

import os
import secrets
from dataclasses import dataclass

from fastapi import Response


@dataclass(frozen=True)
class SessionCookieConfig:
    name: str = os.getenv("APP_SESSION_COOKIE_NAME", "app_session")
    max_age_seconds: int = int(os.getenv("APP_SESSION_MAX_AGE", "28800"))
    secure: bool = os.getenv("APP_COOKIE_SECURE", "true").lower() == "true"
    httponly: bool = True
    samesite: str = os.getenv("APP_COOKIE_SAMESITE", "lax").lower()
    path: str = "/"

    def normalized_samesite(self) -> str:
        allowed = {"lax", "strict", "none"}
        if self.samesite not in allowed:
            return "lax"
        return self.samesite


def new_session_id() -> str:
    return secrets.token_urlsafe(32)


def set_session_cookie(response: Response, session_id: str, config: SessionCookieConfig | None = None) -> None:
    config = config or SessionCookieConfig()
    samesite = config.normalized_samesite()
    secure = config.secure or samesite == "none"

    response.set_cookie(
        key=config.name,
        value=session_id,
        max_age=config.max_age_seconds,
        secure=secure,
        httponly=config.httponly,
        samesite=samesite,
        path=config.path,
    )


def clear_session_cookie(response: Response, config: SessionCookieConfig | None = None) -> None:
    config = config or SessionCookieConfig()
    response.delete_cookie(
        key=config.name,
        path=config.path,
        secure=config.secure,
        httponly=config.httponly,
        samesite=config.normalized_samesite(),
    )
