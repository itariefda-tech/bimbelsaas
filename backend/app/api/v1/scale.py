from flask import Blueprint, g

from app.common.responses import success_response
from app.permissions.decorators import require_auth
from app.services.scale_service import ScaleService

scale_api = Blueprint("scale", __name__)


@scale_api.get("/scale/readiness")
@require_auth
def scale_readiness():
    return success_response(
        data=ScaleService().readiness(g.principal),
        message="Scale readiness loaded.",
    )


@scale_api.get("/scale/smart-scheduling/branches/<uuid:branch_id>/signals")
@require_auth
def smart_scheduling_signals(branch_id):
    return success_response(
        data=ScaleService().smart_scheduling_signals(g.principal, branch_id),
        message="Smart scheduling signals loaded.",
    )
