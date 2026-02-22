from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.auth.msal_store import MSALCacheStore
from apps.api.app.auth.routes import get_auth_service, get_msal_store, router


class MockAuthService:
    def build_authorization_url(self, *, state: str) -> str:
        return f"https://idp.example/authorize?state={state}"

    def exchange_code_for_token(self, *, code: str, redirect_uri: str) -> dict:
        return {
            "access_token": f"token-for-{code}",
            "refresh_token": "refresh-token",
            "redirect_uri": redirect_uri,
            "token_type": "Bearer",
        }


def create_app(storage_path: Path, master_key: str = "test-master-key") -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_auth_service] = lambda: MockAuthService()
    app.dependency_overrides[get_msal_store] = lambda: MSALCacheStore(
        master_key=master_key,
        storage_path=storage_path,
    )
    return app


def test_callback_flow_persists_encrypted_cache(tmp_path: Path) -> None:
    app = create_app(tmp_path / "msal_store.json")

    client = TestClient(app)

    login = client.get("/auth/login", follow_redirects=False)
    assert login.status_code == 302
    assert "oauth_state" in login.cookies

    state = login.cookies["oauth_state"]
    callback = client.get(f"/auth/callback?code=abc123&state={state}")

    assert callback.status_code == 200
    assert callback.json() == {"status": "authenticated"}
    assert "app_session" in callback.cookies

    session_id = callback.cookies["app_session"]
    cache = MSALCacheStore(master_key="test-master-key", storage_path=tmp_path / "msal_store.json")
    restored = cache.load(session_id)
    assert restored is not None
    assert restored["access_token"] == "token-for-abc123"

    raw_file = (tmp_path / "msal_store.json").read_text(encoding="utf-8")
    assert "token-for-abc123" not in raw_file


def test_logout_deletes_cache_and_cookie(tmp_path: Path) -> None:
    storage = tmp_path / "msal_store.json"
    app = create_app(storage)
    client = TestClient(app)

    client.cookies.set("oauth_state", "state")
    callback = client.get("/auth/callback?code=abc123&state=state")
    session_id = callback.cookies["app_session"]

    before = json.loads(storage.read_text(encoding="utf-8"))
    assert session_id in before

    logout = client.post("/auth/logout")
    assert logout.status_code == 204

    after = json.loads(storage.read_text(encoding="utf-8"))
    assert session_id not in after
