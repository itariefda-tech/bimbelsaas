from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(BACKEND_DIR))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BimbelSaaS operational CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init-db",
        help="Create local development database tables.",
    )
    init_parser.set_defaults(handler=init_db)

    seed_parser = subparsers.add_parser(
        "seed-demo",
        help="Seed idempotent demo data for local development.",
    )
    seed_parser.set_defaults(handler=seed_demo)

    smoke_parser = subparsers.add_parser(
        "smoke-check",
        help="Run local app smoke checks through the Flask test client.",
    )
    smoke_parser.add_argument(
        "--email",
        default="owner@example.com",
        help="Demo email to use for the web login check.",
    )
    smoke_parser.add_argument(
        "--password",
        default="password123",
        help="Demo password to use for the web login check.",
    )
    smoke_parser.set_defaults(handler=smoke_check)

    args = parser.parse_args()
    return args.handler(args)


def init_db(_args: argparse.Namespace) -> int:
    from app import create_app
    from app.extensions import db

    app = create_app()
    with app.app_context():
        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        if not database_uri.startswith("sqlite"):
            print(
                "init-db is for local SQLite development. "
                "Use migrations for PostgreSQL staging/production.",
            )
            return 2
        db.create_all()

    print("Local development database tables are ready.")
    return 0


def seed_demo(_args: argparse.Namespace) -> int:
    from scripts.init_demo import main as seed_main

    seed_main()
    return 0


def smoke_check(args: argparse.Namespace) -> int:
    from app import create_app

    app = create_app()
    client = app.test_client()

    login_page = client.get("/login")
    csrf = _extract_csrf(login_page.get_data(as_text=True))
    checks = [
        _check_status("GET /health", client.get("/health"), 200),
        _check_status("GET /login", login_page, 200),
        {"name": "login csrf token present", "ok": bool(csrf)},
    ]

    login = client.post(
        "/login",
        data={
            "email": args.email,
            "password": args.password,
            "_csrf_token": csrf,
        },
        follow_redirects=False,
    )
    checks.append(_check_status("POST /login", login, 302))

    dashboard = client.get("/dashboard", follow_redirects=False)
    checks.append(_check_status("GET /dashboard", dashboard, 302))

    role_dashboard = client.get("/dashboard/platform_owner")
    checks.append(_check_status("GET /dashboard/platform_owner", role_dashboard, 200))
    checks.append(
        {
            "name": "dashboard contains role title",
            "ok": b"Platform Owner Dashboard" in role_dashboard.data,
        }
    )

    print(json.dumps({"checks": checks}, indent=2))
    if all(item["ok"] for item in checks):
        print("Smoke check passed.")
        return 0
    print("Smoke check failed.")
    return 1


def _check_status(name: str, response, expected_status: int) -> dict[str, object]:
    return {
        "name": name,
        "expected_status": expected_status,
        "actual_status": response.status_code,
        "ok": response.status_code == expected_status,
    }


def _extract_csrf(html: str) -> str:
    match = re.search(r'name="_csrf_token" value="([^"]+)"', html)
    return match.group(1) if match else ""


if __name__ == "__main__":
    raise SystemExit(main())
