"""Small package-safe CLI for repository smoke checks."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from . import __author__, __version__
from .config import get_agent_names, is_llm_judge_enabled


def build_info() -> dict[str, object]:
    return {
        "name": "junior-apogee-app",
        "version": __version__,
        "author": __author__,
        "available_agents": get_agent_names(),
        "llm_judge_enabled": is_llm_judge_enabled(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Junior Apogee CLI")
    parser.add_argument(
        "command",
        nargs="?",
        default="info",
        choices=["info"],
        help="Command to run (default: info)",
    )
    args = parser.parse_args(argv)

    if args.command == "info":
        print(json.dumps(build_info(), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
