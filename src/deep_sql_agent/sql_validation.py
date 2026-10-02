# src/deep_sql_agent/sql_validation.py

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from deep_sql_agent.exceptions import SQLValidationError


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    reason: str = ""


class SQLQueryValidator:
    """Validates SQL before execution."""

    _READ_ONLY_START_PATTERN = re.compile(
        r"^\s*(SELECT|WITH)\b",
        re.IGNORECASE,
    )

    _DANGEROUS_KEYWORD_PATTERN = re.compile(
        r"\b("
        r"INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|"
        r"GRANT|REVOKE|MERGE|CALL|EXECUTE"
        r")\b",
        re.IGNORECASE,
    )

    def __init__(self, read_only: bool = True) -> None:
        self._read_only = read_only

    def validate(self, query: Any) -> ValidationResult:
        if not isinstance(query, str):
            return ValidationResult(
                is_valid=False,
                reason="SQL query must be a string.",
            )

        if not query.strip():
            return ValidationResult(
                is_valid=False,
                reason="SQL query must be non-empty.",
            )

        if self._has_multiple_statements(query):
            return ValidationResult(
                is_valid=False,
                reason="SQL query must not contain multiple statements.",
            )

        if self._read_only and not self.is_read_only(query):
            return ValidationResult(
                is_valid=False,
                reason="SQL query must be read-only.",
            )

        return ValidationResult(is_valid=True)

    def is_read_only(self, query: str) -> bool:
        if not isinstance(query, str) or not query.strip():
            return False

        normalized_query = self._strip_single_trailing_semicolon(query)

        if not self._READ_ONLY_START_PATTERN.search(normalized_query):
            return False

        if self._DANGEROUS_KEYWORD_PATTERN.search(normalized_query):
            return False

        return True

    def reject_dangerous_sql(self, query: str) -> None:
        result = self.validate(query)

        if not result.is_valid:
            raise SQLValidationError(result.reason)

    def _has_multiple_statements(self, query: str) -> bool:
        statements = [
            statement.strip()
            for statement in query.split(";")
            if statement.strip()
        ]

        return len(statements) > 1

    def _strip_single_trailing_semicolon(self, query: str) -> str:
        stripped = query.strip()

        if stripped.endswith(";"):
            return stripped[:-1].strip()

        return stripped