from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any

from flask import current_app


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class InMemoryTTLCache:
    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at <= monotonic():
            self._entries.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._entries[key] = CacheEntry(
            value=value,
            expires_at=monotonic() + ttl_seconds,
        )

    def clear(self) -> None:
        self._entries.clear()


cache = InMemoryTTLCache()


def cached_value(key: str, factory, *, ttl_seconds: int | None = None) -> tuple[Any, bool]:
    if not current_app.config.get("CACHE_ENABLED", True):
        return factory(), False
    cached = cache.get(key)
    if cached is not None:
        return cached, True
    value = factory()
    cache.set(
        key,
        value,
        ttl_seconds or current_app.config["CACHE_DEFAULT_TTL_SECONDS"],
    )
    return value, False
