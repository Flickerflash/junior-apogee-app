"""Smoke tests for the Flask dashboard application."""

from __future__ import annotations

from app import app as flask_app


flask_app.config["TESTING"] = True


def test_health_endpoint_returns_ok() -> None:
    client = flask_app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["version"]


def test_snapshot_endpoint_returns_agent_summaries() -> None:
    client = flask_app.test_client()
    response = client.get("/api/v1/snapshot")

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload["agent_summaries"], list)
    assert payload["platform_version"]
