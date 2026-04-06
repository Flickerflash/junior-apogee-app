from __future__ import annotations

from typing import Any

from flask import Flask, abort, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from .config_loader import load_full_config
from .logging_config import configure_logging
from .settings import Settings

REQUEST_COUNTER = Counter("ja_requests_total", "Total HTTP requests received")


def create_app() -> Flask:
    """Construct and return a Flask application for the dashboard."""
    configure_logging()
    app = Flask(__name__)

    @app.before_request
    def before() -> None:
        REQUEST_COUNTER.inc()
        settings = Settings()
        token = settings.api_key
        if token and request.headers.get("Authorization") != f"Bearer {token}":
            abort(401)

    @app.route("/health")
    def health() -> Any:
        return jsonify(status="ok")

    @app.route("/metrics")
    def metrics() -> Any:
        config = load_full_config()
        return jsonify(metrics=config.metrics.dict() if config.metrics else {})

    @app.route("/openapi.json")
    def openapi() -> Any:
        schema = {
            "openapi": "3.0.0",
            "info": {"title": "Junior Apogee API", "version": "0.1.0"},
            "paths": {
                "/health": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/metrics": {"get": {"responses": {"200": {"description": "Metrics"}}}},
            },
        }
        return jsonify(schema)

    @app.route("/prometheus")
    def prometheus_metrics() -> tuple[bytes, int, dict[str, str]]:
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    return app
