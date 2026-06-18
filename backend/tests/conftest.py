import pytest
from uuid import uuid4

from app import create_app
from app.common.cache import cache
from app.config import Config
from app.extensions import db
from app.models.academy import Academy
from app.models.branch import Branch
from app.permissions.constants import Role, ScopeType
from app.services.identity_service import IdentityService


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key-with-at-least-32-bytes"
    SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    LOG_LEVEL = "CRITICAL"
    RATE_LIMIT_ENABLED = False
    OBSERVABILITY_LOG_REQUESTS = False


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        cache.clear()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def identity(app):
    return IdentityService()


@pytest.fixture()
def create_academy(app):
    def factory(
        *,
        name="Test Academy",
        slug=None,
        status="active",
    ):
        academy = Academy(
            name=name,
            slug=slug or f"academy-{uuid4().hex[:10]}",
            timezone="Asia/Jakarta",
            currency="IDR",
            status=status,
        )
        db.session.add(academy)
        db.session.flush()
        return academy

    return factory


@pytest.fixture()
def academy(create_academy):
    return create_academy()


@pytest.fixture()
def academy_id(academy):
    return academy.id


@pytest.fixture()
def create_branch(app):
    def factory(
        *,
        academy_id,
        name="Test Branch",
        code=None,
        status="active",
    ):
        branch = Branch(
            academy_id=academy_id,
            name=name,
            code=code or f"BR-{uuid4().hex[:8].upper()}",
            timezone="Asia/Jakarta",
            status=status,
        )
        db.session.add(branch)
        db.session.flush()
        return branch

    return factory


@pytest.fixture()
def branch(create_branch, academy_id):
    return create_branch(academy_id=academy_id)


@pytest.fixture()
def branch_id(branch):
    return branch.id


@pytest.fixture()
def create_identity(app):
    def factory(
        *,
        academy_id,
        email="operator@example.com",
        password="very-secure-password",
        full_name="Academy Operator",
        assignments=(),
    ):
        service = IdentityService()
        user = service.create_user(
            academy_id=academy_id,
            email=email,
            password=password,
            full_name=full_name,
        )
        created_assignments = [
            service.assign_role(
                user=user,
                role=assignment.get("role", Role.BRANCH_ADMIN),
                scope_type=assignment.get("scope_type", ScopeType.BRANCH),
                academy_id=academy_id,
                branch_id=assignment.get("branch_id"),
                scope_id=assignment.get("scope_id"),
            )
            for assignment in assignments
        ]
        db.session.commit()
        return user, created_assignments

    return factory
