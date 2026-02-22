from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any

from fastapi import Request, Response


SESSION_COOKIE_NAME = "session_id"
CSRF_COOKIE_NAME = "csrf_token"


@dataclass(frozen=True)
class CookieConfig:
    secure: bool = True
    same_site: str = "lax"
    session_max_age: int = 60 * 60


DEFAULT_COOKIE_CONFIG = CookieConfig()


def issue_session_cookies(response: Response, session_id: str, config: CookieConfig = DEFAULT_COOKIE_CONFIG) -> str:
    """Set HttpOnly session cookie and readable CSRF cookie.

    Returns the CSRF token so caller can surface it as needed.
    """
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=config.secure,
        samesite=config.same_site,
        max_age=config.session_max_age,
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=config.secure,
        samesite=config.same_site,
        max_age=config.session_max_age,
    )
    return csrf_token


def verify_csrf(request: Request) -> bool:
    """Double-submit CSRF verification."""
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get("X-CSRF-Token")
    return bool(cookie_token and header_token and secrets.compare_digest(cookie_token, header_token))


def build_audit_record(request: Request, *, action: str, actor_id: str | None) -> dict[str, Any]:
    """Construct audit metadata without body data.

    Intentionally excludes request body and sensitive fields.
    """
    return {
        "action": action,
        "actor_id": actor_id,
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
