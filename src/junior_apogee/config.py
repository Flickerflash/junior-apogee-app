"""Configuration loading helpers for the Junior Apogee platform."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


def _candidate_config_dirs() -> list[Path]:
    configured_dir = os.getenv("JUNIOR_APOGEE_CONFIG_DIR")
    candidates: list[Path] = []

    if configured_dir:
        candidates.append(Path(configured_dir).expanduser())

    package_dir = Path(__file__).resolve().parent
    repo_root = package_dir.parents[2]

    candidates.extend(
        [
            repo_root / "config",
            package_dir / "config",
            package_dir / "config_data",
        ]
    )

    unique_candidates: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in unique_candidates:
            unique_candidates.append(resolved)
    return unique_candidates


def _load_yaml(filename: str) -> dict[str, Any]:
    for config_dir in _candidate_config_dirs():
        filepath = config_dir / filename
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as file_handle:
                return yaml.safe_load(file_handle) or {}

    logger.warning("Config file not found in known locations: {}", filename)
    return {}


@lru_cache(maxsize=1)
def get_agents_config() -> dict[str, Any]:
    return _load_yaml("agents.yaml")


@lru_cache(maxsize=1)
def get_metrics_config() -> dict[str, Any]:
    return _load_yaml("metrics.yaml")


@lru_cache(maxsize=1)
def get_task_families_config() -> dict[str, Any]:
    return _load_yaml("task_families.yaml")


def get_agent_names() -> list[str]:
    config = get_agents_config()
    return [agent["name"] for agent in config.get("agents", [])]


def get_success_bar(family_id: str) -> float:
    """Return the minimum pass rate for a given task family."""
    config = get_task_families_config()
    for family in config.get("task_families", []):
        if family.get("family_id") == family_id:
            return float(family.get("success_bar", 0.85))
    return 0.85


def get_metric_target(metric_name: str, agent: str | None = None) -> float | None:
    config = get_metrics_config()
    for metric in config.get("metrics", []):
        if metric.get("name") != metric_name:
            continue
        if agent and "agent_targets" in metric:
            return float(metric["agent_targets"].get(agent, metric.get("target", 0.0)))
        return float(metric.get("target", 0.0))
    return None


def get_anthropic_api_key() -> str | None:
    return os.getenv("ANTHROPIC_API_KEY")


def get_openai_api_key() -> str | None:
    return os.getenv("OPENAI_API_KEY")


def is_llm_judge_enabled() -> bool:
    return bool(get_anthropic_api_key() or get_openai_api_key())


APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = APP_ENV != "production"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
