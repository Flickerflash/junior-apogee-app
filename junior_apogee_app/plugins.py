from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).parent.parent / "plugins"


def discover_plugins() -> list[str]:
    if not PLUGIN_DIR.exists():
        return []
    return [plugin.stem for plugin in PLUGIN_DIR.glob("*.py")]


def load_plugin(name: str) -> Any:
    module_path = f"plugins.{name}"
    return import_module(module_path)
