"""Flask application factory.

Wires together configuration, extensions (SQLAlchemy, JWT, CORS), the REST API
blueprints and a small set of health / error handlers.
"""
from __future__ import annotations

from flask import Flask, jsonify

from .api import register_blueprints
from .config import Config, get_config
from .extensions import cors, db, jwt


def create_app(config: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config or get_config())

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    register_blueprints(app)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "resource not found"}), 404

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": "internal server error"}), 500

    return app
