import os
from datetime import timedelta


def _normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


class Config:
    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-secret")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://bimbelsaas:bimbelsaas@localhost:5432/bimbelsaas",
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"connect_timeout": 3},
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
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


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    @classmethod
    def validate(cls) -> None:
        super().validate()
        if (
            cls.SECRET_KEY == "development-only-secret"
            or len(cls.SECRET_KEY.encode("utf-8")) < 32
        ):
            raise RuntimeError(
                "SECRET_KEY must contain at least 32 bytes for production."
            )


def get_config() -> type[Config]:
    environment = os.getenv("APP_ENV", "development").lower()
    configurations: dict[str, type[Config]] = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "staging": ProductionConfig,
    }
    try:
        return configurations[environment]
    except KeyError as error:
        raise RuntimeError(f"Unsupported APP_ENV: {environment}") from error
