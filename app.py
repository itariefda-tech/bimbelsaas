import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared for backend installs
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if load_dotenv is not None:
    load_dotenv(ROOT_DIR / ".env")
    load_dotenv(ROOT_DIR / ".env.example")

sys.path.insert(0, str(BACKEND_DIR))

current_app_module = sys.modules.get("app")
if current_app_module is not None:
    current_app_file = Path(getattr(current_app_module, "__file__", "")).resolve()
    if current_app_file == Path(__file__).resolve():
        sys.modules.pop("app", None)

from app import create_app  # noqa: E402
from app.extensions import socketio  # noqa: E402

app = create_app()


if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    debug = os.getenv("APP_ENV", "development").lower() == "development"
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
