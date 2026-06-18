from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from time import monotonic

from flask import Flask, request

from app.common.errors import RateLimitError


@dataclass
class InMemoryRateLimiter:
    buckets: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        now = monotonic()
        bucket = self.buckets[key]
        while bucket and bucket[0] <= now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(window_seconds - (now - bucket[0])))
            raise RateLimitError(retry_after)
        bucket.append(now)


_limiter = InMemoryRateLimiter()


def register_rate_limiter(app: Flask) -> None:
    @app.before_request
    def enforce_rate_limit() -> None:
        if not app.config.get("RATE_LIMIT_ENABLED", True):
            return
        if request.endpoint and request.endpoint.endswith(".liveness"):
            return
        if request.endpoint and request.endpoint.endswith(".readiness"):
            return
        key = _request_key()
        _limiter.check(
            key,
            limit=app.config["RATE_LIMIT_REQUESTS"],
            window_seconds=app.config["RATE_LIMIT_WINDOW_SECONDS"],
        )


def _request_key() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    ip_address = forwarded_for.split(",", 1)[0].strip() or request.remote_addr or "unknown"
    authorization = request.headers.get("Authorization", "")
    if authorization:
        return f"auth:{authorization[-32:]}:{request.method}:{request.path}"
    return f"ip:{ip_address}:{request.method}:{request.path}"
