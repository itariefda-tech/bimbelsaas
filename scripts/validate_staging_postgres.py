from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        print("DATABASE_URL must point to PostgreSQL for staging validation.")
        return 2

    os.environ.setdefault("APP_ENV", "staging")
    os.environ.setdefault("FLASK_APP", "wsgi")
    sys.path.insert(0, str(BACKEND_DIR))

    _run([sys.executable, "-m", "flask", "--app", "wsgi", "db", "upgrade"])

    from app import create_app
    from app.extensions import db

    app = create_app()
    with app.app_context():
        db.session.execute(text("select 1"))
        db.session.commit()

        client = app.test_client()
        live = client.get("/api/v1/health/live")
        ready = client.get("/api/v1/health/ready")

    if live.status_code != 200:
        print(f"Live health failed with status {live.status_code}.")
        return 1
    if ready.status_code != 200:
        print(f"Ready health failed with status {ready.status_code}.")
        return 1

    print("PostgreSQL staging validation passed.")
    print("Migration upgrade completed and health checks returned 200.")
    return 0


def _run(command: list[str]) -> None:
    print(f"Running: {' '.join(command)}")
    subprocess.run(command, cwd=BACKEND_DIR, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
