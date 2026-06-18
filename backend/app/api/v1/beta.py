from flask import Blueprint, g, request

from app.common.responses import success_response
from app.common.validation import (
    json_payload,
    optional_date,
    optional_string,
    optional_uuid,
    required_string,
    required_uuid,
    string_value,
)
from app.permissions.decorators import require_auth
from app.services.beta_service import BetaService

beta_api = Blueprint("beta", __name__)


@beta_api.get("/beta/readiness")
@require_auth
def beta_readiness():
    return success_response(
        data=BetaService().readiness(g.principal),
        message="Beta readiness loaded.",
    )


@beta_api.get("/beta/onboardings")
@require_auth
def list_beta_onboardings():
    onboardings = BetaService().list_onboardings(g.principal)
    return success_response(
        data=[BetaService.serialize_onboarding(item) for item in onboardings],
        message="Beta onboardings loaded.",
    )


@beta_api.post("/beta/onboardings")
@require_auth
def create_beta_onboarding():
    payload = json_payload()
    onboarding = BetaService().create_onboarding(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        cohort_label=required_string(payload, "cohort_label"),
        operational_owner_name=required_string(payload, "operational_owner_name"),
        operational_owner_contact=required_string(payload, "operational_owner_contact"),
        success_criteria=payload.get("success_criteria", {}),
        target_start_date=optional_date(payload.get("target_start_date"), "target_start_date"),
        target_end_date=optional_date(payload.get("target_end_date"), "target_end_date"),
        notes=optional_string(payload, "notes"),
    )
    return success_response(
        data=BetaService.serialize_onboarding(onboarding),
        message="Beta onboarding created.",
        status=201,
    )


@beta_api.patch("/beta/onboardings/<uuid:onboarding_id>/status")
@require_auth
def update_beta_onboarding_status(onboarding_id):
    payload = json_payload()
    onboarding = BetaService().update_onboarding_status(
        g.principal,
        onboarding_id,
        status=required_string(payload, "status"),
        notes=optional_string(payload, "notes"),
    )
    return success_response(
        data=BetaService.serialize_onboarding(onboarding),
        message="Beta onboarding status updated.",
    )


@beta_api.get("/beta/feedback")
@require_auth
def list_beta_feedback():
    feedback = BetaService().list_feedback(
        g.principal,
        academy_id=required_uuid(request.args.get("academy_id"), "academy_id"),
        branch_id=optional_uuid(request.args.get("branch_id"), "branch_id"),
        status=request.args.get("status"),
    )
    return success_response(
        data=[BetaService.serialize_feedback(item) for item in feedback],
        message="Beta feedback loaded.",
    )


@beta_api.post("/beta/feedback")
@require_auth
def submit_beta_feedback():
    payload = json_payload()
    feedback = BetaService().submit_feedback(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=optional_uuid(payload.get("branch_id"), "branch_id"),
        category=required_string(payload, "category"),
        severity=string_value(payload, "severity", "medium"),
        source_role=required_string(payload, "source_role"),
        summary=required_string(payload, "summary"),
        details=optional_string(payload, "details"),
    )
    return success_response(
        data=BetaService.serialize_feedback(feedback),
        message="Beta feedback submitted.",
        status=201,
    )


@beta_api.patch("/beta/feedback/<uuid:feedback_id>/status")
@require_auth
def update_beta_feedback_status(feedback_id):
    payload = json_payload()
    feedback = BetaService().update_feedback_status(
        g.principal,
        feedback_id,
        status=required_string(payload, "status"),
        resolution_notes=optional_string(payload, "resolution_notes"),
    )
    return success_response(
        data=BetaService.serialize_feedback(feedback),
        message="Beta feedback status updated.",
    )
