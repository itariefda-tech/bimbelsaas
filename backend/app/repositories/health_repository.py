from sqlalchemy import text

from app.extensions import db


class HealthRepository:
    @staticmethod
    def database_is_available() -> bool:
        db.session.execute(text("SELECT 1"))
        return True

