"""Utilities for encrypting/decrypting MSAL cache payloads.

Envelope encryption layout:
- Generate a random data encryption key (DEK) per payload.
- Encrypt plaintext with DEK using Fernet.
- Encrypt DEK with APP_MASTER_KEY using Fernet.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any

from cryptography.fernet import Fernet


class MissingMasterKeyError(RuntimeError):
    """Raised when APP_MASTER_KEY is not configured."""


def _get_master_fernet() -> Fernet:
    key = os.getenv("APP_MASTER_KEY")
    if not key:
        raise MissingMasterKeyError("APP_MASTER_KEY is required for MSAL cache encryption")
    return Fernet(key.encode("utf-8"))


def _b64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _b64_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))


def encrypt_blob(payload: bytes) -> str:
    """Encrypt bytes with envelope encryption and return a serialized token string."""
    dek_key = Fernet.generate_key()
    dek_fernet = Fernet(dek_key)
    ciphertext = dek_fernet.encrypt(payload)

    master = _get_master_fernet()
    encrypted_dek = master.encrypt(dek_key)

    envelope: dict[str, Any] = {
        "v": 1,
        "alg": "fernet-envelope",
        "edk": _b64_encode(encrypted_dek),
        "ct": _b64_encode(ciphertext),
    }
    return json.dumps(envelope, separators=(",", ":"))


def decrypt_blob(token: str) -> bytes:
    """Decrypt a token string produced by ``encrypt_blob``."""
    envelope = json.loads(token)
    if envelope.get("v") != 1:
        raise ValueError("Unsupported envelope version")

    master = _get_master_fernet()
    encrypted_dek = _b64_decode(envelope["edk"])
    dek_key = master.decrypt(encrypted_dek)

    ciphertext = _b64_decode(envelope["ct"])
    dek_fernet = Fernet(dek_key)
    return dek_fernet.decrypt(ciphertext)
