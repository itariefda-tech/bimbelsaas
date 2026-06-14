from flask import Blueprint, g, request

from app.common.responses import success_response
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget
from app.permissions.decorators import require_auth
from app.services.authorization_service import AuthorizationService
from app.services.realtime_service import NotificationDeliveryService, RealtimeService
from app.services.financial_service import FinancialService

realtime_api = Blueprint("realtime", __name__)


@realtime_api.post("/operations/realtime/process")
@require_auth
def process_realtime():
    AuthorizationService.require(g.principal, Permission.PLATFORM_MANAGE, AuthorizationTarget())
    limit = request.get_json(silent=True) or {}
    result = RealtimeService().process(limit.get("limit", 100))
    return success_response(data=result, message="Realtime outbox processed.")


@realtime_api.post("/operations/notifications/process")
@require_auth
def process_notifications():
    AuthorizationService.require(g.principal, Permission.PLATFORM_MANAGE, AuthorizationTarget())
    limit = request.get_json(silent=True) or {}
    result = NotificationDeliveryService().process(limit.get("limit", 100))
    return success_response(data=result, message="Notification queue processed.")


@realtime_api.post("/operations/invoices/mark-overdue")
@require_auth
def mark_overdue_invoices():
    AuthorizationService.require(g.principal, Permission.PLATFORM_MANAGE, AuthorizationTarget())
    count = FinancialService().mark_overdue()
    return success_response(data={"updated": count}, message="Overdue invoices reconciled.")
