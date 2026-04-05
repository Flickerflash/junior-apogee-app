from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values


class Settings:
    """Application settings loaded from environment variables or a local env file."""

    def __init__(self, env_file: str = ".env"):
        env_path = Path(env_file)
        file_values = dotenv_values(env_path) if env_path.exists() else {}

        self.api_key = os.getenv("API_KEY") or file_values.get("API_KEY", "")
        self.agent_endpoint = os.getenv("AGENT_ENDPOINT") or file_values.get(
            "AGENT_ENDPOINT", ""
        )
        self.environment = os.getenv("ENVIRONMENT") or file_values.get(
            "ENVIRONMENT", "development"
        )
