"""Shared pytest fixtures for the Junior Apogee test suite.

This file re-exports the src-based fixtures so pytest discovers a single,
conflict-free fixture set across the repository.
"""

from tests.fixtures.conftest import *  # noqa: F401,F403
