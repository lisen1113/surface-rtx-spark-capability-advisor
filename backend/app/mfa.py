"""RFC 6238 TOTP for administrator sign-in; secrets derive from an env-only master key."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
from urllib.parse import quote

from fastapi import HTTPException


def master_key() -> bytes:
    key = os.getenv("CAPABILITY_MFA_MASTER_KEY", "").encode("utf-8")
    if len(key) < 32:
        raise HTTPException(503, "管理员 MFA 密钥尚未配置")
    return key


def user_secret(user_id: int) -> bytes:
    context = b"capability-advisor/admin-totp/v1/" + str(user_id).encode("ascii")
    return hmac.new(master_key(), context, hashlib.sha256).digest()[:20]


def provisioning(user_id: int, email: str) -> dict[str, str]:
    secret = base64.b32encode(user_secret(user_id)).decode("ascii").rstrip("=")
    label = quote("Capability Advisor:" + email, safe="")
    uri = f"otpauth://totp/{label}?secret={secret}&issuer=Capability%20Advisor&algorithm=SHA1&digits=6&period=30"
    return {"secret": secret, "otpauth_uri": uri}


def totp(secret: bytes, counter: int) -> str:
    digest = hmac.new(secret, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def matching_counter(user_id: int, code: str | None, timestamp: float, last_counter: int = -1) -> int | None:
    if not code or len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    secret = user_secret(user_id)
    current = int(timestamp) // 30
    for counter in (current - 1, current, current + 1):
        if counter > last_counter and hmac.compare_digest(totp(secret, counter), code):
            return counter
    return None
