"""
run_eval.py – CLI to run the full test suite (or a subset) and report results.

Usage:
    python scripts/run_eval.py
    python scripts/run_eval.py --layer A_Reasoning
    python scripts/run_eval.py --agent Apogee --layer B_Action
    python scripts/run_eval.py --junit-xml reports/results.xml
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Ensure src is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.junior_apogee.utils.helpers import setup_logger
from loguru import logger


LAYER_TEST_MAP = {
    "A_Reasoning": ["tests/unit/test_layer_a_reasoning.py"],
    "B_Action":    ["tests/unit/test_layer_b_action.py"],
    "C_Outcomes":  ["tests/unit/test_layer_c_outcomes.py"],
    "governance":  ["tests/unit/test_governance.py"],
    "models":      ["tests/unit/test_models.py"],
    "integration": ["tests/integration/"],
}

ALL_TESTS = [
    "tests/unit/",
    "tests/integration/",
]


def main():
    setup_logger("INFO")
    parser = argparse.ArgumentParser(description="Junior Apogee – Test Runner")
    parser.add_argument("--layer", choices=list(LAYER_TEST_MAP.keys()) + ["all"],
                        default="all", help="Test layer to run")
    parser.add_argument("--agent", type=str, default=None,
                        help="Filter tests by agent keyword (used with -k)")
    parser.add_argument("--junit-xml", type=str, default=None,
                        help="Path for JUnit XML output")
    parser.add_argument("--cov", action="store_true",
                        help="Enable coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose pytest output")
    parser.add_argument("--failfast", "-x", action="store_true",
                        help="Stop on first failure")

    args = parser.parse_args()

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    if args.layer == "all":
        cmd.extend(ALL_TESTS)
    else:
        cmd.extend(LAYER_TEST_MAP.get(args.layer, ALL_TESTS))

    if args.agent:
        cmd.extend(["-k", args.agent])

    if args.verbose:
        cmd.append("-v")

    if args.failfast:
        cmd.append("-x")

    if args.junit_xml:
        Path(args.junit_xml).parent.mkdir(parents=True, exist_ok=True)
        cmd.extend([f"--junit-xml={args.junit_xml}"])

    if args.cov:
        cmd.extend(["--cov=src/junior_apogee", "--cov-report=term-missing"])

    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(Path(__file__).parents[1]))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
