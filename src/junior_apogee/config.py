"""
Configuration loader – reads YAML files from the config/ directory
and exposes typed helpers used throughout the platform.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger

CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"


def _load_yaml(filename: str) -> Dict[str, Any]:
    filepath = CONFIG_DIR / filename
    if not filepath.exists():
        logger.warning(f"Config file not found: {filepath}")
        return {}
    with open(filepath, "r") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def get_agents_config() -> Dict[str, Any]:
    return _load_yaml("agents.yaml")


@lru_cache(maxsize=1)
def get_metrics_config() -> Dict[str, Any]:
    return _load_yaml("metrics.yaml")


@lru_cache(maxsize=1)
def get_task_families_config() -> Dict[str, Any]:
    return _load_yaml("task_families.yaml")


def get_agent_names() -> List[str]:
    cfg = get_agents_config()
    return [a["name"] for a in cfg.get("agents", [])]


def get_success_bar(family_id: str) -> float:
    """Return the minimum pass-rate for a given task family."""
    cfg = get_task_families_config()
    for family in cfg.get("task_families", []):
        if family.get("family_id") == family_id:
            return float(family.get("success_bar", 0.85))
    return 0.85


def get_metric_target(metric_name: str, agent: Optional[str] = None) -> Optional[float]:
    cfg = get_metrics_config()
    for m in cfg.get("metrics", []):
        if m.get("name") == metric_name:
            if agent and "agent_targets" in m:
                return float(m["agent_targets"].get(agent, m.get("target", 0.0)))
            return float(m.get("target", 0.0))
    return None


# ─── Environment / secrets ───────────────────────────────────────────────────

def get_anthropic_api_key() -> Optional[str]:
    return os.getenv("ANTHROPIC_API_KEY")


def get_openai_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY")


def is_llm_judge_enabled() -> bool:
    return bool(get_anthropic_api_key() or get_openai_api_key())


APP_ENV      = os.getenv("APP_ENV", "development")
DEBUG        = APP_ENV != "production"
LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO")
FLASK_PORT   = int(os.getenv("FLASK_PORT", "5000"))
FLASK_HOST   = os.getenv("FLASK_HOST", "0.0.0.0")
