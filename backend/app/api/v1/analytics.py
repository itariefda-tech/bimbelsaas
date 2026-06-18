from flask import Blueprint, g, request

from app.common.responses import success_response
from app.common.status_catalog import status_meta
from app.common.validation import optional_date
from app.permissions.decorators import require_auth
from app.services.analytics_service import AnalyticsService

analytics_api = Blueprint("analytics", __name__)


def _period_filters():
    return {
        "start_date": optional_date(request.args.get("from"), "from"),
        "end_date": optional_date(request.args.get("to"), "to"),
    }


@analytics_api.get("/analytics/academies/<uuid:academy_id>/overview")
@require_auth
def academy_overview(academy_id):
    data, cache_hit = AnalyticsService().cached_academy_overview(
        g.principal,
        academy_id,
        **_period_filters(),
    )
    return success_response(
        data=data,
        message="Academy analytics loaded.",
        meta={
            **status_meta(
                "attendance",
                "attendance_sheet",
                "invoice",
                "payment",
                "schedule",
            ),
            "empty_state": {
                "title": "No analytics yet",
                "description": "Operational insights appear after schedules, attendance, and invoices are recorded.",
            },
            "cache": {"hit": cache_hit},
        },
    )


@analytics_api.get("/analytics/branches/<uuid:branch_id>/kpi")
@require_auth
def branch_kpi(branch_id):
    data, cache_hit = AnalyticsService().cached_branch_kpi(
        g.principal,
        branch_id,
        **_period_filters(),
    )
    return success_response(
        data=data,
        message="Branch KPI loaded.",
        meta={
            **status_meta(
                "attendance",
                "attendance_sheet",
                "invoice",
                "payment",
                "schedule",
            ),
            "empty_state": {
                "title": "No branch activity yet",
                "description": "KPIs fill in when this branch has sessions, attendance, or invoices.",
            },
            "cache": {"hit": cache_hit},
        },
    )
