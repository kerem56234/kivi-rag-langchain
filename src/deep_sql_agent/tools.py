# src/deep_sql_agent/tools.py

from __future__ import annotations

from typing import Any


class SQLExecutionTool:
    """Executes SQL only after validation."""

    name = "safe_sql_execution"
    description = "Executes validated read-only SQL against the database."

    def __init__(self, database: Any, validator: Any) -> None:
        raise NotImplementedError

    def run(self, query: str) -> str:
        raise NotImplementedError