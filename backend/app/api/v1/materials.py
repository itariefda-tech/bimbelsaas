from flask import Blueprint, g, request

from app.common.errors import ValidationError
from app.common.responses import success_response
from app.common.validation import (
    json_payload,
    optional_string,
    required_string,
    required_uuid,
)
from app.permissions.decorators import require_auth
from app.services.material_service import MaterialService

materials_api = Blueprint("materials", __name__)


@materials_api.get("/academies/<uuid:academy_id>/materials")
@require_auth
def list_material_repository(academy_id):
    materials = MaterialService().list_repository(g.principal, academy_id)
    return success_response(
        data=[MaterialService.serialize(item) for item in materials],
        message="Material repository loaded.",
    )


@materials_api.post(
    "/branches/<uuid:branch_id>/classes/<uuid:class_id>/materials"
)
@require_auth
def create_material(branch_id, class_id):
    payload = json_payload()
    material = MaterialService().create(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        class_id=class_id,
        material_code=required_string(payload, "material_code"),
        title=required_string(payload, "title"),
        material_type=required_string(payload, "material_type"),
        description=optional_string(payload, "description"),
        file_data=_file_data(payload),
    )
    return success_response(
        data=MaterialService.serialize(material),
        message="Material draft created.",
        status=201,
    )


@materials_api.post(
    "/branches/<uuid:branch_id>/classes/<uuid:class_id>/materials/"
    "<uuid:material_id>/versions"
)
@require_auth
def add_material_version(branch_id, class_id, material_id):
    payload = json_payload()
    version = MaterialService().add_version(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        class_id=class_id,
        material_id=material_id,
        file_data=_file_data(payload),
    )
    return success_response(
        data=MaterialService.serialize_version(version),
        message="Material version uploaded.",
        status=201,
    )


@materials_api.post(
    "/branches/<uuid:branch_id>/classes/<uuid:class_id>/materials/"
    "<uuid:material_id>/versions/<uuid:version_id>/submit"
)
@require_auth
def submit_material_version(branch_id, class_id, material_id, version_id):
    payload = json_payload()
    version = MaterialService().submit_version(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        class_id=class_id,
        material_id=material_id,
        version_id=version_id,
    )
    return success_response(
        data=MaterialService.serialize_version(version),
        message="Material version submitted for review.",
    )


@materials_api.post(
    "/academies/<uuid:academy_id>/materials/<uuid:material_id>/versions/"
    "<uuid:version_id>/approve"
)
@require_auth
def approve_material_version(academy_id, material_id, version_id):
    version = MaterialService().approve_version(
        g.principal,
        academy_id=academy_id,
        material_id=material_id,
        version_id=version_id,
    )
    return success_response(
        data=MaterialService.serialize_version(version),
        message="Material version approved.",
    )


@materials_api.put(
    "/branches/<uuid:branch_id>/classes/<uuid:class_id>/materials/"
    "<uuid:material_id>/distribution"
)
@require_auth
def distribute_material(branch_id, class_id, material_id):
    payload = json_payload()
    distribution = MaterialService().distribute(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        class_id=class_id,
        material_id=material_id,
        version_id=required_uuid(payload.get("version_id"), "version_id"),
    )
    return success_response(
        data=MaterialService.serialize_distribution(distribution),
        message="Material distributed.",
    )


@materials_api.get(
    "/branches/<uuid:branch_id>/classes/<uuid:class_id>/materials"
)
@require_auth
def list_class_materials(branch_id, class_id):
    academy_id = required_uuid(request.args.get("academy_id"), "academy_id")
    distributions = MaterialService().list_for_class(
        g.principal,
        academy_id=academy_id,
        branch_id=branch_id,
        class_id=class_id,
    )
    return success_response(
        data=[
            MaterialService.serialize_distribution(item)
            for item in distributions
        ],
        message="Class materials loaded.",
    )


@materials_api.delete(
    "/academies/<uuid:academy_id>/materials/<uuid:material_id>"
)
@require_auth
def archive_material(academy_id, material_id):
    material = MaterialService().archive(
        g.principal,
        academy_id=academy_id,
        material_id=material_id,
    )
    return success_response(
        data=MaterialService.serialize(material),
        message="Material archived.",
    )


@materials_api.get(
    "/academies/<uuid:academy_id>/materials/<uuid:material_id>/versions/"
    "<uuid:version_id>/access-metadata"
)
@require_auth
def material_access_metadata(academy_id, material_id, version_id):
    metadata = MaterialService().access_metadata(
        g.principal,
        academy_id=academy_id,
        material_id=material_id,
        version_id=version_id,
        branch_id=required_uuid(request.args.get("branch_id"), "branch_id"),
        class_id=required_uuid(request.args.get("class_id"), "class_id"),
        disposition=request.args.get("disposition", "inline"),
    )
    return success_response(data=metadata, message="Material access metadata loaded.")


def _file_data(payload: dict) -> dict[str, object]:
    file_size = payload.get("file_size")
    if isinstance(file_size, bool) or not isinstance(file_size, int) or file_size <= 0:
        raise ValidationError("file_size must be a positive integer.")
    checksum = required_string(payload, "checksum_sha256").lower()
    if len(checksum) != 64 or any(char not in "0123456789abcdef" for char in checksum):
        raise ValidationError("checksum_sha256 must be a 64-character hex digest.")
    return {
        "storage_key": required_string(payload, "storage_key"),
        "file_name": required_string(payload, "file_name"),
        "mime_type": required_string(payload, "mime_type"),
        "file_size": file_size,
        "checksum_sha256": checksum,
    }
