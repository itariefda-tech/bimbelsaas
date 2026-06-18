from flask import Blueprint, g, request

from app.common.responses import success_response
from app.common.validation import optional_date, optional_uuid
from app.permissions.decorators import require_auth
from app.services.export_service import ExportService

exports_api = Blueprint("exports", __name__)


def _period_filters():
    return {
        "start_date": optional_date(request.args.get("from"), "from"),
        "end_date": optional_date(request.args.get("to"), "to"),
    }


def _limit() -> int | None:
    raw_value = request.args.get("limit")
    if raw_value in (None, ""):
        return None
    try:
        return int(raw_value)
    except ValueError:
        from app.common.errors import ValidationError

        raise ValidationError("limit must be an integer.") from None


@exports_api.get("/exports/audit-logs")
@require_auth
def export_audit_logs():
    data = ExportService().audit_logs(
        g.principal,
        academy_id=optional_uuid(request.args.get("academy_id"), "academy_id"),
        branch_id=optional_uuid(request.args.get("branch_id"), "branch_id"),
        limit=_limit(),
        **_period_filters(),
    )
    return success_response(
        data=data,
        message="Audit log export prepared.",
        meta={
            "boundary": "server_capped_json_export",
            "contains_sensitive_fields": False,
        },
    )


@exports_api.get("/exports/reports/branches/<uuid:branch_id>/kpi")
@require_auth
def export_branch_kpi(branch_id):
    data = ExportService().branch_kpi_report(
        g.principal,
        branch_id,
        **_period_filters(),
    )
    return success_response(
        data=data,
        message="Branch KPI report export prepared.",
        meta={"boundary": "server_capped_json_export"},
    )


@exports_api.get("/exports/reports/academies/<uuid:academy_id>/overview")
@require_auth
def export_academy_overview(academy_id):
    data = ExportService().academy_overview_report(
        g.principal,
        academy_id,
        **_period_filters(),
    )
    return success_response(
        data=data,
        message="Academy overview report export prepared.",
        meta={"boundary": "server_capped_json_export"},
    )
