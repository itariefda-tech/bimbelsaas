from unittest.mock import patch


def test_liveness_returns_standard_response(client):
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "test-request"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request"
    assert response.json == {
        "success": True,
        "message": "Service is alive.",
        "data": {"status": "alive"},
        "request_id": "test-request",
    }


def test_readiness_checks_database(client):
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json["data"]["dependencies"]["database"] == "available"


def test_readiness_reports_dependency_failure(client):
    with patch(
        "app.repositories.health_repository.HealthRepository.database_is_available",
        side_effect=RuntimeError("database down"),
    ):
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json["success"] is False
    assert response.json["error"] == {
        "code": "dependency_unavailable",
        "details": {"dependency": "database"},
    }

