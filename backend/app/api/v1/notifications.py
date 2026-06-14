from flask import Blueprint, g, request

from app.common.responses import success_response
from app.permissions.decorators import require_auth
from app.services.notification_service import NotificationService

notifications_api = Blueprint("notifications", __name__)


@notifications_api.get("/notifications")
@require_auth
def list_notifications():
    try:
        limit = int(request.args.get("limit", "20"))
    except ValueError:
        limit = 20
    data = NotificationService().list_for_principal(
        g.principal,
        limit=limit,
        unread_only=request.args.get("unread_only", "false").lower() == "true",
    )
    return success_response(data=data, message="Notifications loaded.")


@notifications_api.patch("/notifications/<uuid:notification_id>/read")
@require_auth
def mark_notification_read(notification_id):
    notification = NotificationService().mark_read(
        g.principal,
        notification_id,
    )
    return success_response(
        data=NotificationService.serialize(notification),
        message="Notification marked as read.",
    )
