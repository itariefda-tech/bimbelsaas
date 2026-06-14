from flask import Blueprint

from app.common.responses import success_response
from app.services.health_service import HealthService

health_api = Blueprint("health", __name__, url_prefix="/health")


@health_api.get("/live")
def liveness():
    return success_response(
        data=HealthService.liveness(),
        message="Service is alive.",
    )


@health_api.get("/ready")
def readiness():
    return success_response(
        data=HealthService.readiness(),
        message="Service is ready.",
    )

