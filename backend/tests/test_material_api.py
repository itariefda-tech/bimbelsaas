from uuid import UUID

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.material_version import MaterialVersion
from app.models.notification import Notification
from app.permissions.constants import Role, ScopeType


def _login(client, email, academy_id):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "academy_id": str(academy_id),
            "email": email,
            "password": "very-secure-password",
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json['data']['access_token']}"}


def _identity(client, create_identity, academy_id, email, assignments):
    user, _ = create_identity(
        academy_id=academy_id,
        email=email,
        assignments=assignments,
    )
    return user, _login(client, email, academy_id)


def _post(client, path, headers, payload):
    response = client.post(path, headers=headers, json=payload)
    assert response.status_code == 201
    return response.json["data"]


def _file(version):
    return {
        "storage_key": f"academy/materials/guide-{version}.pdf",
        "file_name": f"guide-{version}.pdf",
        "mime_type": "application/pdf",
        "file_size": 2048 + version,
        "checksum_sha256": f"{version:064x}",
    }


def _setup(client, create_identity, academy_id, branch_id, suffix):
    _, director_headers = _identity(
        client,
        create_identity,
        academy_id,
        f"material-director-{suffix}@example.com",
        (
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    academic_class = _post(
        client,
        f"/api/v1/branches/{branch_id}/classes",
        director_headers,
        {
            "academy_id": str(academy_id),
            "class_code": f"MAT-{suffix}",
            "class_name": f"Material {suffix}",
            "capacity": 10,
        },
    )
    teacher_user, teacher_headers = _identity(
        client,
        create_identity,
        academy_id,
        f"material-teacher-{suffix}@example.com",
        (
            {
                "role": Role.TEACHER,
                "scope_type": ScopeType.ASSIGNED_CLASS,
                "branch_id": branch_id,
                "scope_id": UUID(academic_class["id"]),
            },
        ),
    )
    return {
        "director_headers": director_headers,
        "teacher_headers": teacher_headers,
        "teacher_user": teacher_user,
        "class": academic_class,
    }


def test_versioned_material_distribution_and_notification_boundary(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _setup(client, create_identity, academy_id, branch_id, "FLOW")
    class_id = setup["class"]["id"]
    created = _post(
        client,
        f"/api/v1/branches/{branch_id}/classes/{class_id}/materials",
        setup["teacher_headers"],
        {
            "academy_id": str(academy_id),
            "material_code": "GUIDE-FLOW",
            "title": "Learning Guide",
            "material_type": "worksheet",
            **_file(1),
        },
    )
    material_id = created["id"]
    first_version = created["latest_version"]
    draft_distribution = client.put(
        (
            f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
            f"{material_id}/distribution"
        ),
        headers=setup["director_headers"],
        json={
            "academy_id": str(academy_id),
            "version_id": first_version["id"],
        },
    )
    submitted = client.post(
        (
            f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
            f"{material_id}/versions/{first_version['id']}/submit"
        ),
        headers=setup["teacher_headers"],
        json={"academy_id": str(academy_id)},
    )
    approved = client.post(
        (
            f"/api/v1/academies/{academy_id}/materials/{material_id}/"
            f"versions/{first_version['id']}/approve"
        ),
        headers=setup["director_headers"],
    )
    distributed = client.put(
        (
            f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
            f"{material_id}/distribution"
        ),
        headers=setup["director_headers"],
        json={
            "academy_id": str(academy_id),
            "version_id": first_version["id"],
        },
    )
    repeated = client.put(
        (
            f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
            f"{material_id}/distribution"
        ),
        headers=setup["director_headers"],
        json={
            "academy_id": str(academy_id),
            "version_id": first_version["id"],
        },
    )
    class_materials = client.get(
        (
            f"/api/v1/branches/{branch_id}/classes/{class_id}/materials"
            f"?academy_id={academy_id}"
        ),
        headers=setup["teacher_headers"],
    )
    notification_list = client.get(
        "/api/v1/notifications",
        headers=setup["teacher_headers"],
    )
    repository = client.get(
        f"/api/v1/academies/{academy_id}/materials",
        headers=setup["teacher_headers"],
    )
    notification_id = notification_list.json["data"]["items"][0]["id"]
    marked = client.patch(
        f"/api/v1/notifications/{notification_id}/read",
        headers=setup["teacher_headers"],
    )

    assert draft_distribution.status_code == 409
    assert draft_distribution.json["error"]["code"] == "material_version_not_ready"
    assert submitted.status_code == 200
    assert approved.status_code == 200
    assert distributed.status_code == 200
    assert repeated.status_code == 200
    assert class_materials.status_code == 200
    assert class_materials.json["data"][0]["version"]["version_label"] == "v1"
    assert notification_list.json["data"]["unread_count"] == 1
    assert repository.status_code == 200
    assert repository.json["data"][0]["material_code"] == "GUIDE-FLOW"
    assert len(notification_list.json["data"]["items"]) == 1
    assert marked.json["data"]["read_at"] is not None
    assert Notification.query.count() == 1
    assert AuditLog.query.filter_by(action_type="material.distributed").count() == 1


def test_new_version_preserves_history_and_updates_distribution(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _setup(client, create_identity, academy_id, branch_id, "VERSION")
    class_id = setup["class"]["id"]
    created = _post(
        client,
        f"/api/v1/branches/{branch_id}/classes/{class_id}/materials",
        setup["teacher_headers"],
        {
            "academy_id": str(academy_id),
            "material_code": "GUIDE-VERSION",
            "title": "Versioned Guide",
            "material_type": "pdf",
            **_file(1),
        },
    )
    material_id = created["id"]
    v1 = created["latest_version"]["id"]
    assert (
        client.post(
            (
                f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
                f"{material_id}/versions/{v1}/submit"
            ),
            headers=setup["teacher_headers"],
            json={"academy_id": str(academy_id)},
        ).status_code
        == 200
    )
    assert (
        client.post(
            (
                f"/api/v1/academies/{academy_id}/materials/{material_id}/"
                f"versions/{v1}/approve"
            ),
            headers=setup["director_headers"],
        ).status_code
        == 200
    )
    assert (
        client.put(
            (
                f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
                f"{material_id}/distribution"
            ),
            headers=setup["director_headers"],
            json={"academy_id": str(academy_id), "version_id": v1},
        ).status_code
        == 200
    )
    v2_response = client.post(
        (
            f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
            f"{material_id}/versions"
        ),
        headers=setup["teacher_headers"],
        json={"academy_id": str(academy_id), **_file(2)},
    )
    v2 = v2_response.json["data"]["id"]
    assert (
        client.post(
            (
                f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
                f"{material_id}/versions/{v2}/submit"
            ),
            headers=setup["teacher_headers"],
            json={"academy_id": str(academy_id)},
        ).status_code
        == 200
    )
    assert (
        client.post(
            (
                f"/api/v1/academies/{academy_id}/materials/{material_id}/"
                f"versions/{v2}/approve"
            ),
            headers=setup["director_headers"],
        ).status_code
        == 200
    )
    updated = client.put(
        (
            f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
            f"{material_id}/distribution"
        ),
        headers=setup["director_headers"],
        json={"academy_id": str(academy_id), "version_id": v2},
    )
    versions = MaterialVersion.query.order_by(
        MaterialVersion.version_number
    ).all()

    assert v2_response.status_code == 201
    assert [item.version_label for item in versions] == ["v1", "v2"]
    assert versions[0].storage_key.endswith("guide-1.pdf")
    assert updated.json["data"]["status"] == "updated"
    assert updated.json["data"]["version"]["version_label"] == "v2"
    assert Notification.query.count() == 2


def test_material_access_is_class_scoped(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _setup(client, create_identity, academy_id, branch_id, "SCOPE")
    class_id = setup["class"]["id"]
    other_class = _post(
        client,
        f"/api/v1/branches/{branch_id}/classes",
        setup["director_headers"],
        {
            "academy_id": str(academy_id),
            "class_code": "MAT-OTHER",
            "class_name": "Other Material Class",
            "capacity": 10,
        },
    )
    _, other_headers = _identity(
        client,
        create_identity,
        academy_id,
        "material-other-teacher@example.com",
        (
            {
                "role": Role.TEACHER,
                "scope_type": ScopeType.ASSIGNED_CLASS,
                "branch_id": branch_id,
                "scope_id": UUID(other_class["id"]),
            },
        ),
    )
    created = _post(
        client,
        f"/api/v1/branches/{branch_id}/classes/{class_id}/materials",
        setup["teacher_headers"],
        {
            "academy_id": str(academy_id),
            "material_code": "GUIDE-SCOPE",
            "title": "Scoped Guide",
            "material_type": "pdf",
            **_file(1),
        },
    )
    material_id = created["id"]
    version_id = created["latest_version"]["id"]
    assert (
        client.post(
            (
                f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
                f"{material_id}/versions/{version_id}/submit"
            ),
            headers=setup["teacher_headers"],
            json={"academy_id": str(academy_id)},
        ).status_code
        == 200
    )
    assert (
        client.post(
            (
                f"/api/v1/academies/{academy_id}/materials/{material_id}/"
                f"versions/{version_id}/approve"
            ),
            headers=setup["director_headers"],
        ).status_code
        == 200
    )
    distributed = client.put(
        (
            f"/api/v1/branches/{branch_id}/classes/{class_id}/materials/"
            f"{material_id}/distribution"
        ),
        headers=setup["director_headers"],
        json={"academy_id": str(academy_id), "version_id": version_id},
    ).json["data"]
    preview_url = distributed["version"]["preview_url"]
    allowed = client.get(preview_url, headers=setup["teacher_headers"])
    denied = client.get(preview_url, headers=other_headers)

    assert allowed.status_code == 200
    assert allowed.json["data"]["delivery"] == "storage_provider_pending"
    assert denied.status_code == 403
