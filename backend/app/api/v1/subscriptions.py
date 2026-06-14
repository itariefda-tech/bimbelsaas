from flask import Blueprint, g

from app.common.responses import success_response
from app.common.validation import json_payload, required_datetime, required_positive_int, required_string, required_uuid
from app.permissions.decorators import require_auth
from app.services.subscription_service import SubscriptionService

subscriptions_api = Blueprint("subscriptions", __name__)


@subscriptions_api.post("/platform/plans")
@require_auth
def create_plan():
    payload = json_payload()
    plan = SubscriptionService().create_plan(
        g.principal,
        code=required_string(payload, "code"),
        name=required_string(payload, "name"),
        price_minor=required_positive_int(payload, "price_minor"),
        features=payload.get("features", []),
    )
    return success_response(data={"id": str(plan.id), "code": plan.code, "features": plan.features}, message="Plan created.", status=201)


@subscriptions_api.post("/platform/subscriptions")
@require_auth
def activate_subscription():
    payload = json_payload()
    item = SubscriptionService().activate(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        plan_id=required_uuid(payload.get("plan_id"), "plan_id"),
        status=required_string(payload, "status"),
        period_end=required_datetime(payload.get("current_period_end"), "current_period_end"),
    )
    return success_response(data=SubscriptionService.serialize_subscription(item), message="Subscription activated.", status=201)


@subscriptions_api.patch("/platform/subscriptions/<uuid:subscription_id>/status")
@require_auth
def transition_subscription(subscription_id):
    payload = json_payload()
    item = SubscriptionService().transition(
        g.principal,
        subscription_id,
        required_string(payload, "status"),
        payload.get("grace_days", 7),
    )
    return success_response(data=SubscriptionService.serialize_subscription(item), message="Subscription updated.")


@subscriptions_api.post("/platform/subscriptions/reconcile")
@require_auth
def reconcile_subscriptions():
    from app.permissions.constants import Permission
    from app.permissions.context import AuthorizationTarget
    from app.services.authorization_service import AuthorizationService

    AuthorizationService.require(
        g.principal,
        Permission.SUBSCRIPTION_MANAGE,
        AuthorizationTarget(),
    )
    data = SubscriptionService().reconcile_expired()
    return success_response(data=data, message="Subscription lifecycle reconciled.")


@subscriptions_api.get("/academies/<uuid:academy_id>/subscription")
@require_auth
def view_subscription(academy_id):
    return success_response(data=SubscriptionService().view(g.principal, academy_id), message="Subscription loaded.")


@subscriptions_api.post("/platform/addons")
@require_auth
def create_addon():
    payload = json_payload()
    item = SubscriptionService().create_addon(
        g.principal,
        code=required_string(payload, "code"),
        name=required_string(payload, "name"),
        feature_key=required_string(payload, "feature_key"),
        price_minor=required_positive_int(payload, "price_minor"),
    )
    return success_response(data={"id": str(item.id), "code": item.code, "feature_key": item.feature_key}, message="Addon created.", status=201)


@subscriptions_api.post("/parent/addons/purchase")
@require_auth
def buy_addon():
    payload = json_payload()
    branch_ids = [
        required_uuid(value, "branch_ids") for value in payload.get("branch_ids", [])
    ]
    item = SubscriptionService().buy_addon(
        g.principal,
        student_id=required_uuid(payload.get("student_id"), "student_id"),
        addon_id=required_uuid(payload.get("addon_id"), "addon_id"),
        branch_ids=branch_ids,
        ends_at=required_datetime(payload["ends_at"], "ends_at") if payload.get("ends_at") else None,
    )
    return success_response(data=SubscriptionService.serialize_addon(item), message="Addon purchased.", status=201)


@subscriptions_api.patch("/parent/addons/<uuid:purchase_id>/cancel")
@require_auth
def cancel_addon(purchase_id):
    item = SubscriptionService().cancel_addon(g.principal, purchase_id)
    return success_response(data=SubscriptionService.serialize_addon(item), message="Addon cancelled.")
