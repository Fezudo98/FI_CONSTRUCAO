import os

from flask import Flask, jsonify

from config import get_config
from app.extensions import db, migrate, bcrypt, cors, limiter
from app.services.errors import ServiceError


def create_app(config_object=None):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object or get_config())

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models  # noqa: F401  (garante que todas as tabelas sejam registradas)
    bcrypt.init_app(app)
    limiter.init_app(app)

    if app.config.get("CORS_ORIGINS"):
        cors.init_app(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    from app.routes.web import bp as web_bp
    from app.routes.api import register_api

    app.register_blueprint(web_bp)
    register_api(app)

    @app.errorhandler(ServiceError)
    def handle_service_error(exc: ServiceError):
        return jsonify({"error": exc.message}), exc.status_code

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    return app
