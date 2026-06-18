import logging
from uuid import uuid4

import pytest

from app import create_app
from app.config import Config, ProductionConfig
from app.extensions import db
from app.models.audit_log import AuditLog
from app.permissions.constants import Role, ScopeType
from tests.conftest import TestConfig


def _login(client, email, academy_id=None):
    payload = {
        "email": email,
        "password": "very-secure-password",
    }
    if academy_id is not None:
        payload["academy_id"] = str(academy_id)
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json['data']['access_token']}"}


def _director(client, create_identity, academy_id):
    user, _ = create_identity(
        academy_id=academy_id,
        email="phase11-director@example.com",
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
        email="phase11-manager@example.com",
        assignments=(
            {
                "role": Role.BRANCH_MANAGER,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    return _login(client, user.email, academy_id)


def _platform_owner(client, create_identity):
    user, _ = create_identity(
        academy_id=None,
        email="phase11-owner@example.com",
        assignments=(
            {
                "role": Role.PLATFORM_OWNER,
                "scope_type": ScopeType.PLATFORM,
            },
        ),
    )
    return _login(client, user.email)


def test_rate_limit_returns_429_and_keeps_request_headers():
    class LimitedConfig(TestConfig):
        RATE_LIMIT_ENABLED = True
        RATE_LIMIT_REQUESTS = 1
        RATE_LIMIT_WINDOW_SECONDS = 60

    app = create_app(LimitedConfig)
    client = app.test_client()

    first = client.get("/missing", headers={"X-Request-ID": "limited-1"})
    second = client.get("/missing", headers={"X-Request-ID": "limited-2"})

    assert first.status_code == 404
    assert second.status_code == 429
    assert second.headers["X-Request-ID"] == "limited-2"
    assert second.headers["X-Response-Time-Ms"] is not None
    assert second.json["error"]["code"] == "rate_limit_exceeded"


def test_request_observability_logs_structured_context(caplog):
    class LoggingConfig(TestConfig):
        OBSERVABILITY_LOG_REQUESTS = True

    app = create_app(LoggingConfig)
    client = app.test_client()

    with caplog.at_level(logging.INFO, logger="app"):
        response = client.get(
            "/api/v1/health/live",
            headers={"X-Request-ID": "observed-request"},
        )

    assert response.status_code == 200
    records = [
        record
        for record in caplog.records
        if record.getMessage() == "request_completed"
    ]
    assert records
    assert records[-1].request_id == "observed-request"
    assert records[-1].path == "/api/v1/health/live"
    assert records[-1].status_code == 200


def test_audit_export_is_permission_scoped_and_server_capped(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    for index in range(3):
        db.session.add(
            AuditLog(
                academy_id=academy_id,
                branch_id=branch_id,
                actor_user_id=None,
                entity_type="phase11",
                entity_id=f"entity-{index}",
                action_type="phase11.checked",
                new_data={"index": index},
                request_id=f"phase11-{index}",
            )
        )
    db.session.commit()

    response = client.get(
        (
            "/api/v1/exports/audit-logs"
            f"?academy_id={academy_id}&branch_id={branch_id}&limit=2"
        ),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json["data"]["row_count"] == 2
    assert response.json["data"]["truncated"] is True
    assert "new_data" not in response.json["data"]["rows"][0]
    assert response.json["meta"]["contains_sensitive_fields"] is False


def test_branch_manager_cannot_export_other_branch_audit_logs(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Export Other")
    headers = _manager(client, create_identity, academy_id, branch_id)

    response = client.get(
        f"/api/v1/exports/audit-logs?branch_id={other_branch.id}",
        headers=headers,
    )

    assert response.status_code == 403


def test_platform_owner_can_export_global_audit_boundary(
    client,
    create_identity,
):
    headers = _platform_owner(client, create_identity)
    audit_log = AuditLog(
        academy_id=None,
        branch_id=None,
        actor_user_id=None,
        entity_type="platform",
        entity_id=str(uuid4()),
        action_type="platform.checked",
    )
    db.session.add(audit_log)
    db.session.commit()

    response = client.get("/api/v1/exports/audit-logs?limit=1", headers=headers)

    assert response.status_code == 200
    assert response.json["data"]["rows"][0]["action_type"] == "platform.checked"


def test_report_export_uses_existing_report_permissions(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)

    response = client.get(
        f"/api/v1/exports/reports/branches/{branch_id}/kpi",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json["data"]["export_type"] == "branch_kpi"
    assert response.json["data"]["row_count"] == 1


def test_production_rejects_disabled_rate_limiting():
    class UnsafeProductionConfig(ProductionConfig):
        SECRET_KEY = "x" * 32
        SQLALCHEMY_DATABASE_URI = "postgresql+psycopg://user:pass@db/app"
        REDIS_URL = "redis://cache:6379/0"
        RATE_LIMIT_ENABLED = False

    with pytest.raises(RuntimeError, match="RATE_LIMIT_ENABLED"):
        UnsafeProductionConfig.validate()


def test_production_rejects_sqlite_database():
    class SqliteProductionConfig(ProductionConfig):
        SECRET_KEY = "x" * 32
        SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///prod.db"
        REDIS_URL = "redis://cache:6379/0"
        RATE_LIMIT_ENABLED = True

    with pytest.raises(RuntimeError, match="SQLite"):
        SqliteProductionConfig.validate()


def test_config_rejects_invalid_limits():
    class InvalidLimitConfig(Config):
        RATE_LIMIT_REQUESTS = 0

    with pytest.raises(RuntimeError, match="RATE_LIMIT_REQUESTS"):
        InvalidLimitConfig.validate()


def test_production_requires_redis_url():
    class MissingRedisProductionConfig(ProductionConfig):
        SECRET_KEY = "x" * 32
        SQLALCHEMY_DATABASE_URI = "postgresql+psycopg://user:pass@db/app"
        REDIS_URL = None
        RATE_LIMIT_ENABLED = True

    with pytest.raises(RuntimeError, match="REDIS_URL"):
        MissingRedisProductionConfig.validate()
