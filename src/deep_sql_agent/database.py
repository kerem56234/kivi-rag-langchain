# src/deep_sql_agent/database.py

from __future__ import annotations

from typing import Any

from langchain_community.utilities import SQLDatabase

from deep_sql_agent.exceptions import DatabaseError


class DatabaseConnector:
    """Creates and checks LangChain SQLDatabase connections."""

    def __init__(self, database_uri: str) -> None:
        if not isinstance(database_uri, str) or not database_uri.strip():
            raise ValueError("database_uri must be a non-empty string.")

        self._database_uri = database_uri

    def create_sql_database(self) -> SQLDatabase:
        try:
            return SQLDatabase.from_uri(self._database_uri)
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