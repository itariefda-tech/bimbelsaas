from datetime import datetime, timedelta, timezone

from app.extensions import db, socketio
from app.models.addon import StudentBranchAccess
from app.models.realtime import NotificationDelivery, RealtimeEvent
from app.permissions.constants import Role, ScopeType
from app.services.entitlement_service import EntitlementService
from app.services.identity_service import IdentityService
from tests.test_parent_experience_api import _setup_parent_data


def _login(client, email, academy_id=None):
    payload = {
        "email": email,
        "password": "very-secure-password",
    }
    if academy_id is not None:
        payload["academy_id"] = str(academy_id)
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json['data']['access_token']}"
    }, response.json["data"]["access_token"]


def _branch_admin(client, identity, academy_id, branch_id):
    user = identity.create_user(
        academy_id=academy_id,
        email="finance-admin@example.com",
        password="very-secure-password",
        full_name="Finance Admin",
    )
    identity.assign_role(
        user=user,
        role=Role.BRANCH_ADMIN,
        scope_type=ScopeType.BRANCH,
        academy_id=academy_id,
        branch_id=branch_id,
    )
    db.session.commit()
    return _login(client, user.email, academy_id)[0]


def _platform_owner(client, identity):
    user = identity.create_user(
        academy_id=None,
        email="owner@example.com",
        password="very-secure-password",
        full_name="Platform Owner",
    )
    identity.assign_role(
        user=user,
        role=Role.PLATFORM_OWNER,
        scope_type=ScopeType.PLATFORM,
    )
    db.session.commit()
    return _login(client, user.email)


def test_invoice_payment_parent_visibility_and_notification_queue(
    client,
    identity,
    academy_id,
    branch_id,
):
    parent = _setup_parent_data(client, identity, academy_id, branch_id)
    admin_headers = _branch_admin(client, identity, academy_id, branch_id)

    created = client.post(
        "/api/v1/financial/invoices",
        headers=admin_headers,
        json={
            "academy_id": str(academy_id),
            "branch_id": str(branch_id),
            "student_id": str(parent["student"].id),
            "invoice_number": "INV-2026-001",
            "description": "July tuition",
            "amount_minor": 150000000,
            "due_date": "2026-07-10",
        },
    )
    assert created.status_code == 201
    invoice_id = created.json["data"]["id"]
    issued = client.patch(
        f"/api/v1/financial/invoices/{invoice_id}/issue",
        headers=admin_headers,
    )
    assert issued.status_code == 200

    visible = client.get(
        "/api/v1/parent/invoices",
        headers=parent["headers"],
    )
    assert visible.status_code == 200
    assert visible.json["data"][0]["invoice_number"] == "INV-2026-001"

    submitted = client.post(
        f"/api/v1/financial/invoices/{invoice_id}/payments",
        headers=parent["headers"],
        json={
            "reference_number": "PAY-001",
            "amount_minor": 150000000,
            "method": "bank_transfer",
            "proof": {
                "storage_key": "proofs/pay-001.jpg",
                "file_name": "pay-001.jpg",
                "mime_type": "image/jpeg",
                "checksum_sha256": "a" * 64,
            },
        },
    )
    assert submitted.status_code == 201
    decided = client.patch(
        f"/api/v1/financial/payments/{submitted.json['data']['id']}/decision",
        headers=admin_headers,
        json={"approve": True},
    )
    assert decided.status_code == 200
    detail = client.get(
        f"/api/v1/financial/invoices/{invoice_id}",
        headers=parent["headers"],
    )
    assert detail.json["data"]["status"] == "paid"
    assert detail.json["data"]["outstanding_minor"] == 0
    assert db.session.query(NotificationDelivery).count() >= 2
    assert db.session.query(RealtimeEvent).count() >= 2


def test_subscription_grace_period_and_cross_branch_addon(
    client,
    identity,
    create_branch,
    academy_id,
    branch_id,
):
    parent = _setup_parent_data(client, identity, academy_id, branch_id)
    target_branch = create_branch(
        academy_id=academy_id,
        name="Second Branch",
        code="SECOND",
    )
    owner_headers, _ = _platform_owner(client, identity)
    plan = client.post(
        "/api/v1/platform/plans",
        headers=owner_headers,
        json={
            "code": "professional",
            "name": "Professional",
            "price_minor": 500000000,
            "features": ["realtime_operations", "advanced_parent_experience"],
        },
    )
    assert plan.status_code == 201
    subscription = client.post(
        "/api/v1/platform/subscriptions",
        headers=owner_headers,
        json={
            "academy_id": str(academy_id),
            "plan_id": plan.json["data"]["id"],
            "status": "active",
            "current_period_end": (
                datetime.now(timezone.utc) + timedelta(days=30)
            ).isoformat(),
        },
    )
    assert subscription.status_code == 201
    grace = client.patch(
        (
            "/api/v1/platform/subscriptions/"
            f"{subscription.json['data']['id']}/status"
        ),
        headers=owner_headers,
        json={"status": "grace_period", "grace_days": 10},
    )
    assert grace.status_code == 200
    assert grace.json["data"]["grace_period_end"] is not None

    addon = client.post(
        "/api/v1/platform/addons",
        headers=owner_headers,
        json={
            "code": "cross-branch",
            "name": "Cross Branch Access",
            "feature_key": "cross_branch_student_access",
            "price_minor": 100000000,
        },
    )
    assert addon.status_code == 201
    purchase = client.post(
        "/api/v1/parent/addons/purchase",
        headers=parent["headers"],
        json={
            "student_id": str(parent["student"].id),
            "addon_id": addon.json["data"]["id"],
            "branch_ids": [str(target_branch.id)],
        },
    )
    assert purchase.status_code == 201
    assert db.session.query(StudentBranchAccess).count() == 1
    assert EntitlementService().student_can_access_branch(
        parent["student"].id,
        target_branch.id,
    )

    cancelled = client.patch(
        f"/api/v1/parent/addons/{purchase.json['data']['id']}/cancel",
        headers=parent["headers"],
    )
    assert cancelled.status_code == 200
    assert not EntitlementService().student_can_access_branch(
        parent["student"].id,
        target_branch.id,
    )

    suspended = client.patch(
        (
            "/api/v1/platform/subscriptions/"
            f"{subscription.json['data']['id']}/status"
        ),
        headers=owner_headers,
        json={"status": "suspended"},
    )
    assert suspended.status_code == 200
    admin_headers = _branch_admin(client, identity, academy_id, branch_id)
    blocked = client.post(
        "/api/v1/financial/invoices",
        headers=admin_headers,
        json={
            "academy_id": str(academy_id),
            "branch_id": str(branch_id),
            "student_id": str(parent["student"].id),
            "invoice_number": "BLOCKED-001",
            "description": "Must be blocked",
            "amount_minor": 10000,
            "due_date": "2026-07-10",
        },
    )
    assert blocked.status_code == 403


def test_socket_authentication_and_deduplicated_realtime_outbox(
    app,
    client,
    identity,
    academy_id,
    branch_id,
):
    parent = _setup_parent_data(client, identity, academy_id, branch_id)
    _, token = _login(client, "parent@example.com", academy_id)
    connected = socketio.test_client(app, auth={"token": token})
    rejected = socketio.test_client(app, auth={"token": "invalid"})
    assert connected.is_connected()
    assert not rejected.is_connected()
    connected.disconnect()

    from app.services.realtime_service import RealtimeService

    service = RealtimeService()
    first = service.enqueue(
        academy_id=academy_id,
        event_type="dashboard.refresh",
        payload={"student_id": str(parent["student"].id)},
        dedup_key="dashboard-refresh-once",
        room=f"student:{parent['student'].id}",
    )
    second = service.enqueue(
        academy_id=academy_id,
        event_type="dashboard.refresh",
        payload={"student_id": str(parent["student"].id)},
        dedup_key="dashboard-refresh-once",
        room=f"student:{parent['student'].id}",
    )
    db.session.commit()
    assert first.id == second.id
    result = service.process()
    assert result == {"processed": 1, "delivered": 1, "failed": 0}
