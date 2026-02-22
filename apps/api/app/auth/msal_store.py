from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from threading import Lock


class MSALStoreError(RuntimeError):
    """Raised when encrypted cache data cannot be processed."""


class MSALCacheStore:
    """Persist encrypted MSAL token cache blobs keyed by session id."""

    _VERSION = b"v1"

    def __init__(self, master_key: str | None = None, storage_path: str | os.PathLike[str] | None = None) -> None:
        master_key = master_key or os.getenv("APP_MASTER_KEY")
        if not master_key:
            raise MSALStoreError("APP_MASTER_KEY must be configured")

        self._master_key = self._normalize_master_key(master_key)
        self._enc_key = hashlib.sha256(self._master_key + b":enc").digest()
        self._mac_key = hashlib.sha256(self._master_key + b":mac").digest()

        default_path = Path(".cache/msal_cache.json")
        self._storage_path = Path(storage_path) if storage_path else default_path
        self._lock = Lock()
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _normalize_master_key(master_key: str) -> bytes:
        try:
            padded = master_key + "=" * (-len(master_key) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
            if decoded:
                return decoded
        except Exception:
            pass
        return master_key.encode("utf-8")

    def _keystream(self, nonce: bytes, length: int) -> bytes:
        out = bytearray()
        counter = 0
        while len(out) < length:
            block = hashlib.sha256(self._enc_key + nonce + counter.to_bytes(4, "big")).digest()
            out.extend(block)
            counter += 1
        return bytes(out[:length])

    def _encrypt(self, plaintext: bytes) -> str:
        nonce = secrets.token_bytes(16)
        keystream = self._keystream(nonce, len(plaintext))
        ciphertext = bytes(a ^ b for a, b in zip(plaintext, keystream))
        mac = hmac.new(self._mac_key, self._VERSION + nonce + ciphertext, hashlib.sha256).digest()
        payload = self._VERSION + nonce + ciphertext + mac
        return base64.urlsafe_b64encode(payload).decode("utf-8")

    def _decrypt(self, blob: str) -> bytes:
        try:
            payload = base64.urlsafe_b64decode(blob.encode("utf-8"))
        except Exception as exc:
            raise MSALStoreError("Cache payload is not valid base64") from exc

        if len(payload) < 2 + 16 + 32:
            raise MSALStoreError("Cache payload is too short")

        version = payload[:2]
        if version != self._VERSION:
            raise MSALStoreError("Unsupported cache payload version")

        nonce = payload[2:18]
        mac = payload[-32:]
        ciphertext = payload[18:-32]

        expected = hmac.new(self._mac_key, version + nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected):
            raise MSALStoreError("Cache payload integrity check failed")

        keystream = self._keystream(nonce, len(ciphertext))
        return bytes(a ^ b for a, b in zip(ciphertext, keystream))

    def _read_all(self) -> dict[str, str]:
        if not self._storage_path.exists():
            return {}

        data = json.loads(self._storage_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise MSALStoreError("Cache storage must contain an object")
        return {str(k): str(v) for k, v in data.items()}

    def _write_all(self, payload: dict[str, str]) -> None:
        self._storage_path.write_text(json.dumps(payload), encoding="utf-8")

    def save(self, session_id: str, cache_data: dict) -> None:
        plaintext = json.dumps(cache_data).encode("utf-8")
        blob = self._encrypt(plaintext)
        with self._lock:
            data = self._read_all()
            data[session_id] = blob
            self._write_all(data)

    def load(self, session_id: str) -> dict | None:
        with self._lock:
            data = self._read_all()
            blob = data.get(session_id)

        if not blob:
            return None

        plaintext = self._decrypt(blob)
        decoded = json.loads(plaintext.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise MSALStoreError("Cache payload did not decode to an object")
        return decoded

    def delete(self, session_id: str) -> None:
        with self._lock:
            data = self._read_all()
            if session_id in data:
                del data[session_id]
                self._write_all(data)
