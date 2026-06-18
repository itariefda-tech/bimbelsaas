from datetime import date, datetime, timezone

from app.extensions import db
from app.models.academic_invoice import AcademicInvoice
from app.models.academic_payment import AcademicPayment
from app.models.notification import Notification
from app.models.parent import Parent
from app.models.parent_student import ParentStudent
from app.models.teacher import Teacher
from app.models.teacher_branch import TeacherBranch
from app.permissions.constants import Role, ScopeType
from tests.test_parent_experience_api import _setup_parent_data


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


def _director(client, create_identity, academy_id):
    user, _ = create_identity(
        academy_id=academy_id,
        email="analytics-director@example.com",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    return _login(client, user.email, academy_id)


def _manager(client, create_identity, academy_id, branch_id):
    user, _ = create_identity(
        academy_id=academy_id,
        email=f"analytics-manager-{branch_id}@example.com",
        assignments=(
            {
                "role": Role.BRANCH_MANAGER,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    return _login(client, user.email, academy_id)


def _add_financials_and_engagement(identity, academy_id, branch_id, student_id):
    user = identity.create_user(
        academy_id=academy_id,
        email="analytics-parent@example.com",
        password="very-secure-password",
        full_name="Analytics Parent",
    )
    parent = Parent(
        academy_id=academy_id,
        user_id=user.id,
        relationship_type="guardian",
        primary_contact=True,
        status="active",
    )
    db.session.add(parent)
    db.session.flush()
    db.session.add(
        ParentStudent(
            academy_id=academy_id,
            parent_id=parent.id,
            student_id=student_id,
            relationship_status="active",
            linked_by=user.id,
        )
    )
    invoice = AcademicInvoice(
        academy_id=academy_id,
        branch_id=branch_id,
        student_id=student_id,
        invoice_number="AN-INV-001",
        description="Analytics tuition",
        currency="IDR",
        amount_minor=200000,
        paid_minor=125000,
        due_date=date(2026, 7, 10),
        status="partially_paid",
        created_by=user.id,
        issued_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )
    db.session.add(invoice)
    db.session.flush()
    db.session.add_all(
        [
            AcademicPayment(
                academy_id=academy_id,
                branch_id=branch_id,
                invoice_id=invoice.id,
                reference_number="AN-PAY-001",
                amount_minor=125000,
                method="bank_transfer",
                status="confirmed",
                submitted_by=user.id,
                confirmed_by=user.id,
                submitted_at=datetime(2026, 7, 3, tzinfo=timezone.utc),
                confirmed_at=datetime(2026, 7, 3, tzinfo=timezone.utc),
            ),
            Notification(
                academy_id=academy_id,
                recipient_user_id=user.id,
                notification_type="attendance.finalized",
                priority="normal",
                title="Attendance finalized",
                payload={"branch_id": str(branch_id)},
                dedup_key="analytics-attendance-finalized",
            ),
        ]
    )


def test_branch_kpi_combines_operational_attendance_revenue_and_ui_meta(
    client,
    identity,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _setup_parent_data(client, identity, academy_id, branch_id)
    db.session.add(
        TeacherBranch(
            academy_id=academy_id,
            teacher_id=Teacher.query.filter_by(academy_id=academy_id).one().id,
            branch_id=branch_id,
            assignment_status="active",
        )
    )
    _add_financials_and_engagement(
        identity,
        academy_id,
        branch_id,
        setup["student"].id,
    )
    db.session.commit()
    headers = _director(client, create_identity, academy_id)

    response = client.get(
        f"/api/v1/analytics/branches/{branch_id}/kpi?from=2026-07-01&to=2026-07-31",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json["data"]["scheduled_sessions"] == 2
    assert response.json["data"]["completed_sessions"] == 1
    assert response.json["data"]["attendance"]["by_status"]["present"] == 1
    assert response.json["data"]["attendance"]["by_status"]["absent"] == 1
    assert response.json["data"]["revenue"]["issued_revenue_minor"] == 200000
    assert response.json["data"]["revenue"]["collected_revenue_minor"] == 125000
    assert response.json["data"]["parent_engagement"]["linked_students"] == 1
    assert response.json["meta"]["status_catalog"]["invoice"]["paid"]["tone"] == "success"


def test_academy_overview_lists_branch_totals_and_empty_state(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)

    response = client.get(
        f"/api/v1/analytics/academies/{academy_id}/overview",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json["data"]["totals"]["active_students"] == 0
    assert response.json["data"]["branches"][0]["branch_id"] == str(branch_id)
    assert response.json["meta"]["empty_state"]["title"] == "No analytics yet"


def test_branch_manager_cannot_view_other_branch_analytics(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Other Analytics")
    headers = _manager(client, create_identity, academy_id, branch_id)

    response = client.get(
        f"/api/v1/analytics/branches/{other_branch.id}/kpi",
        headers=headers,
    )

    assert response.status_code == 403


def test_status_catalog_endpoint_supports_phase_9_ui_consistency(
    client,
    create_identity,
    academy_id,
):
    headers = _director(client, create_identity, academy_id)

    response = client.get("/api/v1/ui/status-catalog", headers=headers)

    assert response.status_code == 200
    assert response.json["data"]["schedule"]["pending_approval"]["tone"] == "warning"
    assert response.json["meta"]["density"]["mobile"] == "compact"
