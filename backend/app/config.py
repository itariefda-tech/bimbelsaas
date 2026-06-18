import os
from datetime import timedelta


def _normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


def _engine_options(database_uri: str) -> dict[str, object]:
    if database_uri.startswith("sqlite"):
        return {"pool_pre_ping": True}
    return {
        "connect_args": {"connect_timeout": 3},
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }


class Config:
    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "development-only-secret-key-change-before-production",
    )
    BETA_LAUNCH_ENABLED = os.getenv("BETA_LAUNCH_ENABLED", "false").lower() == "true"
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_DEFAULT_TTL_SECONDS = int(os.getenv("CACHE_DEFAULT_TTL_SECONDS", "60"))
    REDIS_URL = os.getenv("REDIS_URL")
    QUEUE_WORKER_CONCURRENCY = int(os.getenv("QUEUE_WORKER_CONCURRENCY", "1"))
    REALTIME_WORKER_CONCURRENCY = int(os.getenv("REALTIME_WORKER_CONCURRENCY", "1"))
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "120"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    EXPORT_MAX_ROWS = int(os.getenv("EXPORT_MAX_ROWS", "1000"))
    OBSERVABILITY_LOG_REQUESTS = (
        os.getenv("OBSERVABILITY_LOG_REQUESTS", "true").lower() == "true"
    )
    DEMO_LOGIN_HINTS_ENABLED = (
        os.getenv("DEMO_LOGIN_HINTS_ENABLED", "true").lower() == "true"
    )
    DEMO_SEED_ENABLED = os.getenv("DEMO_SEED_ENABLED", "true").lower() == "true"
    DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "password123")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            "sqlite:///dev.db",
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options(SQLALCHEMY_DATABASE_URI)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    JSON_SORT_KEYS = False
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TTL = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TTL_MINUTES", "15"))
    )
    JWT_REFRESH_TTL = timedelta(
        days=int(os.getenv("JWT_REFRESH_TTL_DAYS", "30"))
    )
    TEACHER_MIN_TRANSITION_MINUTES = int(
        os.getenv("TEACHER_MIN_TRANSITION_MINUTES", "30")
    )
    TEACHER_DAILY_SESSION_WARNING = int(
        os.getenv("TEACHER_DAILY_SESSION_WARNING", "6")
    )

    @classmethod
    def validate(cls) -> None:
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise RuntimeError("DATABASE_URL must be configured.")
        if cls.RATE_LIMIT_REQUESTS <= 0:
            raise RuntimeError("RATE_LIMIT_REQUESTS must be greater than zero.")
        if cls.RATE_LIMIT_WINDOW_SECONDS <= 0:
            raise RuntimeError(
                "RATE_LIMIT_WINDOW_SECONDS must be greater than zero."
            )
        if cls.EXPORT_MAX_ROWS <= 0:
            raise RuntimeError("EXPORT_MAX_ROWS must be greater than zero.")
        if cls.CACHE_DEFAULT_TTL_SECONDS <= 0:
            raise RuntimeError("CACHE_DEFAULT_TTL_SECONDS must be greater than zero.")
        if cls.QUEUE_WORKER_CONCURRENCY <= 0:
            raise RuntimeError("QUEUE_WORKER_CONCURRENCY must be greater than zero.")
        if cls.REALTIME_WORKER_CONCURRENCY <= 0:
            raise RuntimeError(
                "REALTIME_WORKER_CONCURRENCY must be greater than zero."
            )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PREFERRED_URL_SCHEME = "https"
    DEMO_LOGIN_HINTS_ENABLED = False
    DEMO_SEED_ENABLED = False

    @classmethod
    def validate(cls) -> None:
        super().validate()
        if (
            cls.SECRET_KEY
            in {
                "development-only-secret",
                "development-only-secret-key-change-before-production",
            }
            or len(cls.SECRET_KEY.encode("utf-8")) < 32
        ):
            raise RuntimeError(
                "SECRET_KEY must contain at least 32 bytes for production."
            )
        if not cls.RATE_LIMIT_ENABLED:
            raise RuntimeError("RATE_LIMIT_ENABLED must be true for production.")
        if cls.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
            raise RuntimeError("Production DATABASE_URL must not use SQLite.")
        if not cls.REDIS_URL:
            raise RuntimeError("REDIS_URL must be configured for production.")
        if cls.DEMO_LOGIN_HINTS_ENABLED:
            raise RuntimeError("DEMO_LOGIN_HINTS_ENABLED must be false for production.")
        if cls.DEMO_SEED_ENABLED:
            raise RuntimeError("DEMO_SEED_ENABLED must be false for production.")


class StagingConfig(ProductionConfig):
    BETA_LAUNCH_ENABLED = True
    DEMO_LOGIN_HINTS_ENABLED = False
    DEMO_SEED_ENABLED = False


def get_config() -> type[Config]:
    environment = os.getenv("APP_ENV", "development").lower()
    configurations: dict[str, type[Config]] = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "staging": StagingConfig,
    }
    try:
        return configurations[environment]
    except KeyError as error:
        raise RuntimeError(f"Unsupported APP_ENV: {environment}") from error
