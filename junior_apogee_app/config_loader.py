from pathlib import Path
from typing import Any

import yaml

from .models import Config


def load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file_handle:
        return yaml.safe_load(file_handle)


def load_config(
    name: str,
    config_dir: Path = Path(__file__).parent.parent / "config",
) -> dict[str, Any]:
    """Read a YAML config file by name."""
    path = config_dir / f"{name}.yaml"
    return load_yaml(path)


def load_full_config(
    config_dir: Path = Path(__file__).parent.parent / "config",
) -> Config:
    """Load and validate all top-level config files into a single object."""
    return Config(
        task_families=load_yaml(config_dir / "task_families.yaml").get("task_families"),
        metrics=load_yaml(config_dir / "metrics.yaml"),
        agents=load_yaml(config_dir / "agents.yaml").get("agents"),
    )
