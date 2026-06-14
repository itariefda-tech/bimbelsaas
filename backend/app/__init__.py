import logging

from flask import Flask

from app.api import register_api
from app.common.errors import register_error_handlers
from app.common.request_context import register_request_context
from app.config import Config, get_config
from app.extensions import db, migrate


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    selected_config = config_object or get_config()
    app.config.from_object(selected_config)
    selected_config.validate()
    app.logger.setLevel(logging.getLevelName(app.config["LOG_LEVEL"]))

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models  # noqa: F401

    register_request_context(app)
    register_error_handlers(app)
    register_api(app)

    return app
