# src/deep_sql_agent/database.py

from __future__ import annotations

from typing import Any

from langchain_community.utilities import SQLDatabase

from deep_sql_agent.exceptions import DatabaseError


class DatabaseConnector:
    """Creates and checks LangChain SQLDatabase connections."""

    def __init__(
        self,
        database_uri: str,
        include_tables: tuple[str, ...] | None = None,
    ) -> None:
        if not isinstance(database_uri, str) or not database_uri.strip():
            raise ValueError(
                "database_uri must be a non-empty string."
            )

        self._validate_include_tables(include_tables)

        self._database_uri = database_uri
        self.include_tables = include_tables

    def create_sql_database(self) -> SQLDatabase:
        try:
            options: dict[str, Any] = {
                "sample_rows_in_table_info": 0,
            }

            if self.include_tables is not None:
                options["include_tables"] = list(
                    self.include_tables
                )

            return SQLDatabase.from_uri(
                self._database_uri,
                **options,
            )
        except Exception as exc:
            raise DatabaseError(
                "Failed to create LangChain SQLDatabase."
            ) from exc

    def test_connection(self, database: Any) -> bool:
        try:
            database.run("SELECT 1")
            return True
        except Exception:
            return False

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

        if any(
            not isinstance(table_name, str)
            or not table_name.strip()
            for table_name in include_tables
        ):
            raise ValueError(
                "include_tables must contain non-empty strings."
            )