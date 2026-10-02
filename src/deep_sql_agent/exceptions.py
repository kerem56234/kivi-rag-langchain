# src/deep_sql_agent/exceptions.py

from __future__ import annotations


class AgentError(Exception):
    """Base exception for all deep SQL agent errors."""


class SQLValidationError(AgentError):
    """Raised when a SQL query fails validation."""