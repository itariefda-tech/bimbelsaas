from flask import Blueprint

from app.api.v1.analytics import analytics_api
from app.api.v1.auth import auth_api
from app.api.v1.beta import beta_api
from app.api.v1.exports import exports_api
from app.api.v1.financial import financial_api
from app.api.v1.health import health_api
from app.api.v1.materials import materials_api
from app.api.v1.notifications import notifications_api
from app.api.v1.organizations import organizations_api
from app.api.v1.parent_experience import parent_experience_api
from app.api.v1.realtime import realtime_api
from app.api.v1.people import people_api
from app.api.v1.scale import scale_api
from app.api.v1.scheduling import scheduling_api
from app.api.v1.teacher_workflow import teacher_workflow_api
from app.api.v1.subscriptions import subscriptions_api
from app.api.v1.ui import ui_api

api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api_v1.register_blueprint(analytics_api)
api_v1.register_blueprint(auth_api)
api_v1.register_blueprint(beta_api)
api_v1.register_blueprint(exports_api)
api_v1.register_blueprint(financial_api)
api_v1.register_blueprint(health_api)
api_v1.register_blueprint(materials_api)
api_v1.register_blueprint(notifications_api)
api_v1.register_blueprint(organizations_api)
api_v1.register_blueprint(parent_experience_api)
api_v1.register_blueprint(realtime_api)
api_v1.register_blueprint(people_api)
api_v1.register_blueprint(scale_api)
api_v1.register_blueprint(scheduling_api)
api_v1.register_blueprint(teacher_workflow_api)
api_v1.register_blueprint(subscriptions_api)
api_v1.register_blueprint(ui_api)
