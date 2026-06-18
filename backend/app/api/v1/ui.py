from flask import Blueprint

from app.common.responses import success_response
from app.common.status_catalog import STATUS_CATALOG
from app.permissions.decorators import require_auth

ui_api = Blueprint("ui", __name__)


@ui_api.get("/ui/status-catalog")
@require_auth
def status_catalog():
    return success_response(
        data=STATUS_CATALOG,
        message="Status catalog loaded.",
        meta={
            "tones": ["success", "warning", "danger", "info", "neutral", "muted"],
            "density": {
                "mobile": "compact",
                "desktop": "comfortable",
            },
        },
    )
