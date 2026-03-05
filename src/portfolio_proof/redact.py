from __future__ import annotations

from typing import Any


_SENSITIVE_KEYWORDS = (
    "token",
    "password",
    "secret",
    "apikey",
    "api_key",
    "access_key",
    "private_key",
    "credentials",
)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            key = str(k)
            if _is_sensitive_key(key):
                out[key] = "<redacted>"
            else:
                out[key] = redact(v)
        return out
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, tuple):
        return tuple(redact(v) for v in value)
    return value


def _is_sensitive_key(key: str) -> bool:
    k = key.lower()
    if any(word in k for word in _SENSITIVE_KEYWORDS):
        return True
    return False

