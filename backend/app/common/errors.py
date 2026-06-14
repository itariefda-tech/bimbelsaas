from dataclasses import dataclass, field
from typing import Any

from flask import Flask, current_app
from werkzeug.exceptions import HTTPException

from app.common.responses import error_response


@dataclass
class AppError(Exception):
    message: str
    code: str = "application_error"
    status_code: int = 400
    details: dict[str, Any] = field(default_factory=dict)


class DependencyUnavailableError(AppError):
    def __init__(self, dependency: str) -> None:
        super().__init__(
            message=f"{dependency} is unavailable.",
            code="dependency_unavailable",
            status_code=503,
            details={"dependency": dependency},
        )


class AuthenticationError(AppError):
    def __init__(
        self,
        message: str = "Authentication is required.",
        code: str = "authentication_required",
    ) -> None:
        super().__init__(message=message, code=code, status_code=401)


class AuthorizationError(AppError):
    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        code: str = "permission_denied",
    ) -> None:
        super().__init__(message=message, code=code, status_code=403)


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "conflict") -> None:
        super().__init__(message=message, code=code, status_code=409)


class SchedulingConflictError(AppError):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        stage: str,
        conflicting_schedule_ids: list[str] | None = None,
    ) -> None:
        details: dict[str, Any] = {"stage": stage}
        if conflicting_schedule_ids:
            details["conflicting_schedule_ids"] = conflicting_schedule_ids
        super().__init__(
            message=message,
            code=code,
            status_code=409,
            details=details,
        )


class NotFoundError(AppError):
    def __init__(self, resource: str) -> None:
        super().__init__(
            message=f"{resource} was not found.",
            code="not_found",
            status_code=404,
        )


class ValidationError(AppError):
    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="validation_error",
            status_code=422,
            details=details or {},
        )


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return error_response(
            message=error.message,
            code=error.code,
            status=error.status_code,
            details=error.details,
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return error_response(
            message=error.description,
            code=error.name.lower().replace(" ", "_"),
            status=error.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        current_app.logger.exception("Unhandled application error", exc_info=error)
        return error_response(
            message="An unexpected error occurred.",
            code="internal_server_error",
            status=500,
        )
