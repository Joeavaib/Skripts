from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException, Request, Response, status

from .session import build_audit_record, issue_session_cookies, verify_csrf

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(response: Response) -> dict[str, str]:
    """Create a session and issue CSRF-safe cookies."""
    session_id = secrets.token_urlsafe(32)
    csrf_token = issue_session_cookies(response=response, session_id=session_id)
    return {"csrf_token": csrf_token}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    if not verify_csrf(request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")

    response.delete_cookie("session_id")
    response.delete_cookie("csrf_token")

    _ = build_audit_record(request, action="auth.logout", actor_id=None)
    return {"status": "ok"}
