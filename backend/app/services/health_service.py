from app.common.errors import DependencyUnavailableError
from app.repositories.health_repository import HealthRepository


class HealthService:
    @staticmethod
    def liveness() -> dict[str, str]:
        return {"status": "alive"}

    @staticmethod
    def readiness() -> dict[str, object]:
        try:
            database_ready = HealthRepository.database_is_available()
        except Exception as error:
            raise DependencyUnavailableError("database") from error

        return {
            "status": "ready",
            "dependencies": {
                "database": "available" if database_ready else "unavailable",
            },
        }

