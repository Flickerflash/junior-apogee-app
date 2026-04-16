__version__ = "0.1.0b0"

This package is retained for backward-compatibility only.
All canonical code lives in src/junior_apogee/.
Do NOT add new functionality here.
This shim will be removed in v1.0.0.
"""
import warnings

warnings.warn(
    "'junior_apogee_app' is a deprecated compatibility shim. "
    "Import from 'junior_apogee' (src/junior_apogee/) instead. "
    "This shim will be removed in v1.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

def main() -> None:
    """Entry point for ``python -m junior_apogee_app``."""
    from .cli import cli

# Re-export main entry point so `python -m junior_apogee_app` still works
def main() -> None:  # noqa: D103
    """Thin wrapper — delegates to canonical CLI in src/junior_apogee."""
    try:
        from junior_apogee.cli import cli  # type: ignore[import]
    except ImportError:  # fallback if src not yet on path
        from .cli import cli  # type: ignore[import]
    cli()
