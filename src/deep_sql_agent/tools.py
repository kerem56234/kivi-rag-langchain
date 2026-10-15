# src/deep_sql_agent/tools.py

from __future__ import annotations

from typing import Any

from deep_sql_agent.exceptions import DatabaseError, SQLValidationError

from langchain_core.tools import BaseTool

class SQLExecutionTool:
    """Executes SQL only after validation."""

    name = "safe_sql_execution"
    description = "Executes validated read-only SQL against the database."

    def __init__(self, database: Any, validator: Any) -> None:
        if database is None:
            raise ValueError("database must not be None.")

        if validator is None:
            raise ValueError("validator must not be None.")

        self._database = database
        self._validator = validator

    def run(self, query: str) -> str:
        validation_result = self._validator.validate(query)

        if not validation_result.is_valid:
            raise SQLValidationError(validation_result.reason)

        try:
            return self._database.run(query)
        except Exception as exc:
            raise DatabaseError(
                "Failed to execute SQL query."
            ) from exc

    def as_langchain_tool(self) -> BaseTool:
        """Expose this safe executor as a LangChain tool."""
        raise NotImplementedError