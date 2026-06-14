import pytest

from app.config import ProductionConfig, _normalize_database_url


def test_legacy_postgres_url_is_normalized_for_psycopg():
    assert (
        _normalize_database_url("postgres://user:pass@db/app")
        == "postgresql+psycopg://user:pass@db/app"
    )


def test_postgresql_url_is_normalized_for_psycopg():
    assert (
        _normalize_database_url("postgresql://user:pass@db/app")
        == "postgresql+psycopg://user:pass@db/app"
    )


def test_production_rejects_development_secret():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        ProductionConfig.validate()
