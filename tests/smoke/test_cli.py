"""Smoke tests for the packaged Junior Apogee CLI."""

from __future__ import annotations

from junior_apogee.cli import build_info, main


def test_build_info_exposes_expected_fields() -> None:
    info = build_info()

    assert info["name"] == "junior-apogee-app"
    assert isinstance(info["available_agents"], list)
    assert "version" in info
    assert "author" in info


def test_cli_info_command_returns_success() -> None:
    assert main(["info"]) == 0
