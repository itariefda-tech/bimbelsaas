from typing import Any

from flask import g, jsonify


def success_response(
    *,
    data: Any = None,
    message: str = "Operation completed.",
    status: int = 200,
    meta: dict[str, Any] | None = None,
):
    payload: dict[str, Any] = {
        "success": True,
        "message": message,
        "data": data,
        "request_id": g.get("request_id"),
    }
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), status


def error_response(
    *,
    message: str,
    code: str,
    status: int,
    details: dict[str, Any] | None = None,
):
    return (
        jsonify(
            {
                "success": False,
                "message": message,
                "error": {
                    "code": code,
                    "details": details or {},
                },
                "request_id": g.get("request_id"),
            }
        ),
        status,
    )

