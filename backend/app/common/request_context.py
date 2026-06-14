from uuid import uuid4

from flask import Flask, g, request


def register_request_context(app: Flask) -> None:
    @app.before_request
    def assign_request_id() -> None:
        g.request_id = request.headers.get("X-Request-ID") or str(uuid4())

    @app.after_request
    def expose_request_id(response):
        response.headers["X-Request-ID"] = g.request_id
        return response

