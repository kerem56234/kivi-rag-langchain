# src/deep_sql_agent/settings.py

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppSettings:
    """Validated application configuration."""

    database_uri: str
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:latest"
    temperature: float = 0.0
    include_tables: tuple[str, ...] | None = None

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
        self._validate_include_tables(self.include_tables)

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
        raw_include_tables = os.getenv("DEEP_SQL_INCLUDE_TABLES")

        try:
            temperature = float(raw_temperature)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "DEEP_SQL_TEMPERATURE must be a number between 0 and 2."
            ) from exc

        include_tables = cls._parse_include_tables(
            raw_include_tables
        )

        try:
            return cls(
                database_uri=database_uri,
                ollama_base_url=ollama_base_url,
                ollama_model=ollama_model,
                temperature=temperature,
                include_tables=include_tables,
            )
        except ValueError as exc:
            if "temperature must be" in str(exc):
                raise ValueError(
                    "DEEP_SQL_TEMPERATURE must be a number between 0 and 2."
                ) from exc

            raise

    @classmethod
    def _parse_include_tables(
        cls,
        raw_value: str | None,
    ) -> tuple[str, ...] | None:
        if raw_value is None:
            return None

        if not raw_value.strip():
            raise ValueError(
                "DEEP_SQL_INCLUDE_TABLES must contain valid table names."
            )

        raw_parts = raw_value.split(",")

        if any(not part.strip() for part in raw_parts):
            raise ValueError(
                "DEEP_SQL_INCLUDE_TABLES must contain valid table names."
            )

        include_tables = tuple(
            part.strip()
            for part in raw_parts
        )

        try:
            cls._validate_include_tables(include_tables)
        except ValueError as exc:
            raise ValueError(
                "DEEP_SQL_INCLUDE_TABLES must contain unique "
                "SQL identifier table names."
            ) from exc

        return include_tables

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

    @staticmethod
    def _validate_include_tables(
        include_tables: tuple[str, ...] | None,
    ) -> None:
        if include_tables is None:
            return

        if (
            not isinstance(include_tables, tuple)
            or not include_tables
        ):
            raise ValueError(
                "include_tables must be a non-empty tuple or None."
            )

        identifier_pattern = re.compile(
            r"^[A-Za-z_][A-Za-z0-9_]*$"
        )

        if any(
            not isinstance(table_name, str)
            or not identifier_pattern.fullmatch(table_name)
            for table_name in include_tables
        ):
            raise ValueError(
                "include_tables must contain valid SQL identifiers."
            )

        if len(set(include_tables)) != len(include_tables):
            raise ValueError(
                "include_tables must not contain duplicates."
            )