from __future__ import annotations

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from prometheus_flask_exporter import PrometheusMetrics

from src.config import resolve_config


db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


_metrics = None


def create_app(config_object=None):
    app = Flask(__name__)

    config_class = resolve_config(config_object)
    if hasattr(config_class, "validate"):
        config_class.validate()

    app.config.from_object(config_class)

    Swagger(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    global _metrics
    if _metrics is None:
        _metrics = PrometheusMetrics.for_app_factory()
    _metrics.init_app(app)
    _metrics.info("app_info", "Schedule system", version="1.0.0")

    from src.app import models  # noqa: F401
    from src.app.routes import register_blueprints

    register_blueprints(app, api_prefix="/api")
    return app
