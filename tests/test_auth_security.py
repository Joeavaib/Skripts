from __future__ import annotations

from cryptography.fernet import Fernet
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from apps.api.app.auth.msal_store import decrypt_blob, encrypt_blob
from apps.api.app.auth.routes import router
from apps.api.app.auth.session import build_audit_record


def test_msal_blob_roundtrip_encryption(monkeypatch):
    monkeypatch.setenv("APP_MASTER_KEY", Fernet.generate_key().decode("utf-8"))
    payload = b'{"access_token":"super-secret"}'

    encrypted = encrypt_blob(payload)

    assert encrypted != payload.decode("utf-8")
    assert decrypt_blob(encrypted) == payload


def test_login_sets_secure_cookie_flags():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.post("/auth/login")

    set_cookie = response.headers.get_list("set-cookie")
    assert any("session_id=" in c and "HttpOnly" in c and "Secure" in c and "SameSite=lax" in c for c in set_cookie)
    assert any("csrf_token=" in c and "Secure" in c and "SameSite=lax" in c for c in set_cookie)


def test_audit_record_excludes_message_body():
    app = FastAPI()

    @app.post("/audit")
    async def endpoint(request: Request):
        return build_audit_record(request, action="test.action", actor_id="u-123")

    client = TestClient(app)
    response = client.post(
        "/audit",
        json={"message": "super secret payload", "password": "dont-log-me"},
        headers={"user-agent": "pytest-agent"},
    )

    record = response.json()
    assert "message" not in record
    assert "password" not in record
    assert "body" not in record
    assert "super secret payload" not in str(record)
    assert record["action"] == "test.action"
