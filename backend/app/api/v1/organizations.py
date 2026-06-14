from flask import Blueprint, g

from app.common.responses import success_response
from app.common.validation import (
    json_payload,
    optional_string,
    required_string,
    string_value,
)
from app.permissions.decorators import require_auth
from app.services.academy_service import AcademyService
from app.services.branch_analytics_service import BranchAnalyticsService
from app.services.branch_service import BranchService

organizations_api = Blueprint("organizations", __name__)


@organizations_api.get("/academies")
@require_auth
def list_academies():
    academies = AcademyService().list_visible(g.principal)
    return success_response(
        data=[AcademyService.serialize(academy) for academy in academies],
        message="Academies loaded.",
    )


@organizations_api.post("/academies")
@require_auth
def create_academy():
    payload = json_payload()
    academy = AcademyService().create(
        g.principal,
        name=required_string(payload, "name"),
        slug=required_string(payload, "slug"),
        timezone_name=string_value(payload, "timezone", "Asia/Jakarta"),
        currency=string_value(payload, "currency", "IDR"),
        logo_url=optional_string(payload, "logo_url"),
    )
    return success_response(
        data=AcademyService.serialize(academy),
        message="Academy created.",
        status=201,
    )


@organizations_api.get("/academies/<uuid:academy_id>")
@require_auth
def get_academy(academy_id):
    academy = AcademyService().get_visible(g.principal, academy_id)
    return success_response(
        data=AcademyService.serialize(academy),
        message="Academy loaded.",
    )


@organizations_api.patch("/academies/<uuid:academy_id>")
@require_auth
def update_academy(academy_id):
    academy = AcademyService().update(
        g.principal,
        academy_id,
        json_payload(require_nonempty=True),
    )
    return success_response(
        data=AcademyService.serialize(academy),
        message="Academy updated.",
    )


@organizations_api.delete("/academies/<uuid:academy_id>")
@require_auth
def archive_academy(academy_id):
    academy = AcademyService().archive(g.principal, academy_id)
    return success_response(
        data=AcademyService.serialize(academy),
        message="Academy archived.",
    )


@organizations_api.get("/academies/<uuid:academy_id>/branches")
@require_auth
def list_branches(academy_id):
    branches = BranchService().list_visible(g.principal, academy_id)
    return success_response(
        data=[BranchService.serialize(branch) for branch in branches],
        message="Branches loaded.",
    )


@organizations_api.post("/academies/<uuid:academy_id>/branches")
@require_auth
def create_branch(academy_id):
    payload = json_payload()
    branch = BranchService().create(
        g.principal,
        academy_id,
        name=required_string(payload, "name"),
        code=required_string(payload, "code"),
        timezone_name=string_value(payload, "timezone", "Asia/Jakarta"),
        address=optional_string(payload, "address"),
    )
    return success_response(
        data=BranchService.serialize(branch),
        message="Branch created.",
        status=201,
    )


@organizations_api.get("/branches/<uuid:branch_id>")
@require_auth
def get_branch(branch_id):
    branch = BranchService().get_visible(g.principal, branch_id)
    return success_response(
        data=BranchService.serialize(branch),
        message="Branch loaded.",
    )


@organizations_api.patch("/branches/<uuid:branch_id>")
@require_auth
def update_branch(branch_id):
    branch = BranchService().update(
        g.principal,
        branch_id,
        json_payload(require_nonempty=True),
    )
    return success_response(
        data=BranchService.serialize(branch),
        message="Branch updated.",
    )


@organizations_api.delete("/branches/<uuid:branch_id>")
@require_auth
def archive_branch(branch_id):
    branch = BranchService().archive(g.principal, branch_id)
    return success_response(
        data=BranchService.serialize(branch),
        message="Branch archived.",
    )


@organizations_api.get("/branches/<uuid:branch_id>/summary")
@require_auth
def branch_summary(branch_id):
    return success_response(
        data=BranchAnalyticsService().summary(g.principal, branch_id),
        message="Branch summary loaded.",
    )
