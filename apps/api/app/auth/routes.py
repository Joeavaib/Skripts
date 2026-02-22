from __future__ import annotations

import os
import secrets
from typing import Protocol
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse

from .msal_store import MSALCacheStore
from .session import SessionCookieConfig, clear_session_cookie, new_session_id, set_session_cookie

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthService(Protocol):
    def build_authorization_url(self, *, state: str) -> str: ...

    def exchange_code_for_token(self, *, code: str, redirect_uri: str) -> dict: ...


class DefaultAuthService:
    def build_authorization_url(self, *, state: str) -> str:
        authority = os.getenv("APP_AUTH_AUTHORITY", "https://login.microsoftonline.com/common/oauth2/v2.0/authorize")
        params = {
            "client_id": os.getenv("APP_AUTH_CLIENT_ID", "dev-client"),
            "response_type": "code",
            "redirect_uri": os.getenv("APP_AUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"),
            "scope": os.getenv("APP_AUTH_SCOPES", "openid profile email").replace(",", " "),
            "state": state,
        }
        return f"{authority}?{urlencode(params)}"

    def exchange_code_for_token(self, *, code: str, redirect_uri: str) -> dict:
        raise NotImplementedError("Wire a real MSAL token exchange service in dependency injection")


def get_auth_service() -> AuthService:
    return DefaultAuthService()


def get_msal_store() -> MSALCacheStore:
    return MSALCacheStore()


@router.get("/login")
def login(request: Request, auth_service: AuthService = Depends(get_auth_service)) -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    authorization_url = auth_service.build_authorization_url(state=state)

    response = RedirectResponse(url=authorization_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return response


@router.get("/callback")
def callback(
    request: Request,
    code: str,
    state: str,
    auth_service: AuthService = Depends(get_auth_service),
    cache_store: MSALCacheStore = Depends(get_msal_store),
) -> JSONResponse:
    expected_state = request.cookies.get("oauth_state")
    if not expected_state or state != expected_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")

    redirect_uri = os.getenv("APP_AUTH_REDIRECT_URI", "http://localhost:8000/auth/callback")
    token_payload = auth_service.exchange_code_for_token(code=code, redirect_uri=redirect_uri)

    session_cfg = SessionCookieConfig()
    session_id = request.cookies.get(session_cfg.name) or new_session_id()
    cache_store.save(session_id, token_payload)

    response = JSONResponse({"status": "authenticated"})
    set_session_cookie(response, session_id, session_cfg)
    response.delete_cookie("oauth_state", path="/", secure=True, httponly=True, samesite="lax")
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    cache_store: MSALCacheStore = Depends(get_msal_store),
) -> Response:
    session_cfg = SessionCookieConfig()
    session_id = request.cookies.get(session_cfg.name)
    if session_id:
        cache_store.delete(session_id)

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookie(response, session_cfg)
    return response
