from uuid import uuid4
from time import perf_counter

from flask import Flask, g, request


def register_request_context(app: Flask) -> None:
    @app.before_request
    def assign_request_id() -> None:
        g.request_id = request.headers.get("X-Request-ID") or str(uuid4())
        g.request_started_at = perf_counter()

    @app.after_request
    def expose_request_id(response):
        response.headers["X-Request-ID"] = g.request_id
        duration_ms = round(
            (perf_counter() - g.get("request_started_at", perf_counter())) * 1000,
            2,
        )
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        if app.config.get("OBSERVABILITY_LOG_REQUESTS", True):
            app.logger.info(
                "request_completed",
                extra={
                    "request_id": g.request_id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "remote_addr": request.headers.get(
                        "X-Forwarded-For",
                        request.remote_addr,
                    ),
                },
            )
        return response
