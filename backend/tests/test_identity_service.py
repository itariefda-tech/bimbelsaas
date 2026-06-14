import pytest
from werkzeug.security import check_password_hash

from app.common.errors import ConflictError, ValidationError
from app.extensions import db
from app.models.audit_log import AuditLog
from app.permissions.constants import Role, ScopeType
from app.services.identity_service import IdentityService


def test_identity_password_is_hashed(identity, academy_id):
    user = identity.create_user(
        academy_id=academy_id,
        email="USER@EXAMPLE.COM",
        password="very-secure-password",
        full_name="User Name",
    )

    assert user.email == "user@example.com"
    assert user.password_hash != "very-secure-password"
    assert check_password_hash(user.password_hash, "very-secure-password")


def test_role_scope_combination_is_validated(identity, academy_id, branch_id):
    user = identity.create_user(
        academy_id=academy_id,
        email="user@example.com",
        password="very-secure-password",
        full_name="User Name",
    )

    with pytest.raises(ValidationError, match="academy_director"):
        identity.assign_role(
            user=user,
            role=Role.ACADEMY_DIRECTOR,
            scope_type=ScopeType.BRANCH,
            academy_id=academy_id,
            branch_id=branch_id,
        )


def test_role_assignment_is_audited(identity, academy_id, branch_id):
    user = identity.create_user(
        academy_id=academy_id,
        email="user@example.com",
        password="very-secure-password",
        full_name="User Name",
    )
    identity.assign_role(
        user=user,
        role=Role.BRANCH_ADMIN,
        scope_type=ScopeType.BRANCH,
        academy_id=academy_id,
        branch_id=branch_id,
    )
    db.session.commit()

    audit = AuditLog.query.filter_by(action_type="role.assigned").one()
    assert audit.academy_id == academy_id
    assert audit.branch_id == branch_id


def test_duplicate_role_assignment_is_rejected(identity, academy_id, branch_id):
    user = identity.create_user(
        academy_id=academy_id,
        email="user@example.com",
        password="very-secure-password",
        full_name="User Name",
    )
    assignment = {
        "user": user,
        "role": Role.BRANCH_ADMIN,
        "scope_type": ScopeType.BRANCH,
        "academy_id": academy_id,
        "branch_id": branch_id,
    }
    identity.assign_role(**assignment)

    with pytest.raises(ConflictError, match="already assigned"):
        identity.assign_role(**assignment)
