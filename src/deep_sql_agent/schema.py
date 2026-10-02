# src/deep_sql_agent/schema.py

from __future__ import annotations

from typing import Any


class SQLSchemaProvider:
    """Provides schema information from a LangChain SQLDatabase."""

    def __init__(self, database: Any) -> None:
        if database is None:
            raise ValueError("database must not be None.")

        self._database = database

    def get_table_names(self) -> list[str]:
        return list(self._database.get_usable_table_names())

    def get_schema_context(self) -> str:
        return self._database.get_table_info()

    def get_table_info(self, table_names: list[str]) -> str:
        self._validate_table_names(table_names)

        return self._database.get_table_info(table_names)

    def _validate_table_names(self, table_names: list[str]) -> None:
        if not isinstance(table_names, list):
            raise ValueError("table_names must be a list.")

        if not table_names:
            raise ValueError("table_names must not be empty.")

        for table_name in table_names:
            if not isinstance(table_name, str) or not table_name.strip():
                raise ValueError(
                    "Each table name must be a non-empty string."
                )