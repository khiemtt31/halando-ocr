from __future__ import annotations

from datetime import timedelta
from typing import Any

import jwt

from app.core.auth.base import Principal, clean_roles, extract_roles
from app.core.auth.local import LocalAuthProvider
from app.core.time import utcnow


def create_signed_token(payload: dict[str, Any], secret_key: str, ttl_seconds: int) -> str:
    now = utcnow()
    claims = {
        **payload,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "iss": "doc-ocr-api",
    }
    return jwt.encode(claims, secret_key, algorithm="HS256")


def decode_signed_token(token: str, secret_key: str) -> dict[str, Any]:
    return jwt.decode(token, secret_key, algorithms=["HS256"], options={"verify_aud": False})


__all__ = [
    "LocalAuthProvider",
    "Principal",
    "clean_roles",
    "create_signed_token",
    "decode_signed_token",
    "extract_roles",
]
