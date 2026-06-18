from app import create_app
from app.config import ProductionConfig
from app.extensions import db
from app.permissions.constants import Role, ScopeType
from tests.conftest import TestConfig


def _csrf_from_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    marker = 'name="_csrf_token" value="'
    body = response.get_data(as_text=True)
    start = body.index(marker) + len(marker)
    end = body.index('"', start)
    return body[start:end]


def test_login_rejects_missing_csrf_token(client):
    response = client.post(
        "/login",
        data={"email": "owner@example.com", "password": "password123"},
    )

    assert response.status_code == 400


def test_login_accepts_valid_csrf_token(client, create_identity):
    user, _ = create_identity(
        academy_id=None,
        email="web-owner@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.PLATFORM_OWNER,
                "scope_type": ScopeType.PLATFORM,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    response = client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_session_cookie_security_defaults():
    app = create_app(TestConfig)

    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_production_rejects_demo_login_hints():
    class UnsafeProductionConfig(ProductionConfig):
        SECRET_KEY = "x" * 32
        SQLALCHEMY_DATABASE_URI = "postgresql+psycopg://user:pass@db/app"
        REDIS_URL = "redis://cache:6379/0"
        RATE_LIMIT_ENABLED = True
        DEMO_LOGIN_HINTS_ENABLED = True
        DEMO_SEED_ENABLED = False

    try:
        UnsafeProductionConfig.validate()
    except RuntimeError as error:
        assert "DEMO_LOGIN_HINTS_ENABLED" in str(error)
    else:
        raise AssertionError("Expected production demo hints to be rejected.")
