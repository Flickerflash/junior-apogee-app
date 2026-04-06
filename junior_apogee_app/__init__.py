__version__ = "0.1.0b0"

# import side-effects (agent registrations, etc.)
from . import agents_example  # noqa: F401


def main() -> None:
    """Entry point for ``python -m junior_apogee_app``."""
    from .cli import cli

    cli()
