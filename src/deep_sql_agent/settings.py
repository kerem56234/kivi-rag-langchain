# src/deep_sql_agent/settings.py

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppSettings:
    """Validated application configuration."""

    database_uri: str
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:latest"
    temperature: float = 0.0

    def __post_init__(self) -> None:
        self._validate_non_empty_string(
            self.database_uri,
            "database_uri",
        )
        self._validate_non_empty_string(
            self.ollama_base_url,
            "ollama_base_url",
        )
        self._validate_non_empty_string(
            self.ollama_model,
            "ollama_model",
        )
        self._validate_temperature(
            self.temperature,
            "temperature",
        )

    @classmethod
    def from_env(cls) -> "AppSettings":
        database_uri = os.getenv("DEEP_SQL_DATABASE_URI")

        if not isinstance(database_uri, str) or not database_uri.strip():
            raise ValueError(
                "DEEP_SQL_DATABASE_URI must be a non-empty string."
            )

        ollama_base_url = os.getenv(
            "DEEP_SQL_OLLAMA_BASE_URL",
            "http://localhost:11434",
        )
        ollama_model = os.getenv(
            "DEEP_SQL_OLLAMA_MODEL",
            "qwen3:latest",
        )
        raw_temperature = os.getenv(
            "DEEP_SQL_TEMPERATURE",
            "0.0",
        )

        try:
            temperature = float(raw_temperature)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "DEEP_SQL_TEMPERATURE must be a number between 0 and 2."
            ) from exc

        try:
            return cls(
                database_uri=database_uri,
                ollama_base_url=ollama_base_url,
                ollama_model=ollama_model,
                temperature=temperature,
            )
        except ValueError as exc:
            if "temperature must be" in str(exc):
                raise ValueError(
                    "DEEP_SQL_TEMPERATURE must be a number between 0 and 2."
                ) from exc

            raise

    @staticmethod
    def _validate_non_empty_string(
        value: Any,
        field_name: str,
    ) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field_name} must be a non-empty string."
            )

    @staticmethod
    def _validate_temperature(
        value: Any,
        field_name: str,
    ) -> None:
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or value < 0
            or value > 2
        ):
            raise ValueError(
                f"{field_name} must be a number between 0 and 2."
            )