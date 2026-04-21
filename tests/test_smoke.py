"""Smoke tests for Issue #6 - dashboard startup + legacy shim deprecation.

Tests:
  1. Flask app object is importable and is a Flask instance.
  2. Flask app has required routes registered (/, /health, /api/v1/agents).
  3. Legacy junior_apogee_app import emits DeprecationWarning.
  4. CLI entry-point is callable (tests/legacy shim delegates to .cli.cli).
  5. src.junior_apogee core modules are importable without side-effects.

All tests must pass with no external services running (no LLM calls, no DB).
"""
import importlib
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup - ensure repo root is on sys.path so `app` and `src` are found
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ===========================================================================
# Smoke Test 1: Flask app object importable
# ===========================================================================
def test_flask_app_importable():
    """app.py must export a Flask instance named `app`."""
    import app as dashboard_app  # noqa: PLC0415
    from flask import Flask

    assert isinstance(dashboard_app.app, Flask), (
        "dashboard_app.app is not a Flask instance - startup will fail"
    )


# ===========================================================================
# Smoke Test 2: Required routes registered
# ===========================================================================
def test_dashboard_required_routes():
    """Flask app must have at minimum /, /health, and /api/v1/agents routes."""
    import app as dashboard_app  # noqa: PLC0415

    registered = {rule.rule for rule in dashboard_app.app.url_map.iter_rules()}
    required_routes = {"/", "/health", "/api/v1/agents"}
    missing = required_routes - registered
    assert not missing, f"Missing required routes: {missing}"


# ===========================================================================
# Smoke Test 3: Legacy shim emits DeprecationWarning on import
# ===========================================================================
def test_legacy_shim_emits_deprecation_warning():
    """Importing junior_apogee_app must raise DeprecationWarning (Issue #3)."""
    # Remove cached module so the warning fires fresh
    for mod in list(sys.modules.keys()):
        if mod.startswith("junior_apogee_app"):
            del sys.modules[mod]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.import_module("junior_apogee_app")
    deprecation_warnings = [
        w for w in caught if issubclass(w.category, DeprecationWarning)
    ]
    assert deprecation_warnings, (
        "junior_apogee_app did not emit DeprecationWarning - shim not applied"
    )


# ===========================================================================
# Smoke Test 4: src.junior_apogee core modules importable
# ===========================================================================
@pytest.mark.parametrize(
    "module_path",
    [
        "src.junior_apogee",
        "src.junior_apogee.models",
        "src.junior_apogee.config",
    ],
)
def test_core_modules_importable(module_path: str):
    """Core src modules must be importable without raising."""
    mod = importlib.import_module(module_path)
    assert mod is not None, f"Failed to import {module_path}"


# ===========================================================================
# Smoke Test 5: CLI help exits 0 (subprocess - no external deps needed)
# ===========================================================================
def test_cli_info_exits_cleanly():
    """python -m junior_apogee_app --help must exit 0 (CLI delegate smoke)."""
    result = subprocess.run(
        [sys.executable, "-m", "junior_apogee_app", "--help"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=15,
    )
    assert result.returncode == 0, (
        f"CLI --help exited {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
