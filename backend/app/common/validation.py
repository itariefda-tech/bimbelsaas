from datetime import date, datetime, timezone
from uuid import UUID

from flask import request

from app.common.errors import ValidationError


def json_payload(*, require_nonempty: bool = False) -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("A JSON object is required.")
    if require_nonempty and not payload:
        raise ValidationError("At least one field is required.")
    return payload


def required_string(payload: dict, field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(
            f"{field} is required.",
            details={field: "required"},
        )
    return value.strip()


def string_value(payload: dict, field: str, default: str) -> str:
    value = payload.get(field, default)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string.")
    return value.strip()


def optional_string(payload: dict, field: str) -> str | None:
    value = payload.get(field)
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string.")
    return value.strip()


def optional_uuid(value: object, field: str) -> UUID | None:
    if value in (None, ""):
        return None
    try:
        return UUID(str(value))
    except ValueError as error:
        raise ValidationError(
            f"{field} must be a valid UUID.",
            details={field: "invalid_uuid"},
        ) from error


def required_uuid(value: object, field: str) -> UUID:
    result = optional_uuid(value, field)
    if result is None:
        raise ValidationError(
            f"{field} is required.",
            details={field: "required"},
        )
    return result


def optional_date(value: object, field: str) -> date | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must use YYYY-MM-DD format.")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field} must use YYYY-MM-DD format.") from error


def required_datetime(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(
            f"{field} is required and must be an ISO 8601 datetime."
        )
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValidationError(f"{field} must be an ISO 8601 datetime.") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValidationError(f"{field} must include a timezone offset.")
    return parsed.astimezone(timezone.utc)


def required_positive_int(payload: dict, field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(
            f"{field} must be a positive integer.",
            details={field: "invalid_positive_integer"},
        )
    return value
