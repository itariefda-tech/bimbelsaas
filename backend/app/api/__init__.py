from flask import Flask

from app.api.v1 import api_v1


def register_api(app: Flask) -> None:
    app.register_blueprint(api_v1)

