"""
Centralised configuration loader.

Reads from an optional `.env` file **and** environment variables,
then exposes a frozen dataclass so the rest of the codebase stays
clean and testable.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(override=False)  # `.env` is optional

@dataclass(frozen=True, slots=True)
class Config:
    """Immutable runtime configuration."""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", 3306))
    database: str = os.getenv("DB_NAME", "geodata")
    user: str = os.getenv("DB_USER", "ro")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    @staticmethod
    def from_env() -> "Config":
        """Factory reading current process environment."""
        return Config()  # type: ignore[arg-type]
