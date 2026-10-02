# src/deep_sql_agent/database.py

from __future__ import annotations

from typing import Any

from langchain_community.utilities import SQLDatabase


class DatabaseConnector:
    """Creates and checks LangChain SQLDatabase connections."""

    def __init__(self, database_uri: str) -> None:
        raise NotImplementedError

    def create_sql_database(self) -> SQLDatabase:
        raise NotImplementedError

    def test_connection(self, database: Any) -> bool:
        raise NotImplementedError