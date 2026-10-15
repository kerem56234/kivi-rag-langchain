# tests/test_tools.py

from unittest.mock import MagicMock

import pytest

from deep_sql_agent.exceptions import DatabaseError, SQLValidationError
from deep_sql_agent.sql_validation import ValidationResult
from deep_sql_agent.tools import SQLExecutionTool
from langchain_core.tools import BaseTool

def test_run_validates_query_before_execution():
    database = MagicMock()
    database.run.return_value = "[(1, 'Alice')]"

    validator = MagicMock()
    validator.validate.return_value = ValidationResult(is_valid=True)

    tool = SQLExecutionTool(database=database, validator=validator)

    result = tool.run("SELECT * FROM customers")

    assert result == "[(1, 'Alice')]"
    validator.validate.assert_called_once_with("SELECT * FROM customers")
    database.run.assert_called_once_with("SELECT * FROM customers")


def test_run_rejects_invalid_sql_before_database_execution():
    database = MagicMock()

    validator = MagicMock()
    validator.validate.return_value = ValidationResult(
        is_valid=False,
        reason="SQL query must be read-only.",
    )

    tool = SQLExecutionTool(database=database, validator=validator)

    with pytest.raises(SQLValidationError, match="read-only"):
        tool.run("DROP TABLE customers")

    database.run.assert_not_called()


def test_run_wraps_database_execution_errors():
    database = MagicMock()
    database.run.side_effect = RuntimeError("database unavailable")

    validator = MagicMock()
    validator.validate.return_value = ValidationResult(is_valid=True)

    tool = SQLExecutionTool(database=database, validator=validator)

    with pytest.raises(DatabaseError, match="Failed to execute SQL query") as error:
        tool.run("SELECT * FROM customers")

    assert isinstance(error.value.__cause__, RuntimeError)


def test_constructor_rejects_missing_database():
    validator = MagicMock()

    with pytest.raises(ValueError, match="database must not be None"):
        SQLExecutionTool(database=None, validator=validator)


def test_constructor_rejects_missing_validator():
    database = MagicMock()

    with pytest.raises(ValueError, match="validator must not be None"):
        SQLExecutionTool(database=database, validator=None)


def test_tool_exposes_name_and_description():
    database = MagicMock()
    validator = MagicMock()

    tool = SQLExecutionTool(database=database, validator=validator)

    assert tool.name == "safe_sql_execution"
    assert "validated read-only sql" in tool.description.lower()

# ============================================================
# LangChain tool adapter
# ============================================================

def test_as_langchain_tool_returns_base_tool():
    database = MagicMock()
    validator = MagicMock()

    execution_tool = SQLExecutionTool(
        database=database,
        validator=validator,
    )

    langchain_tool = execution_tool.as_langchain_tool()

    assert isinstance(langchain_tool, BaseTool)
    assert langchain_tool.name == "safe_sql_execution"
    assert langchain_tool.description == execution_tool.description


def test_langchain_tool_invocation_delegates_to_safe_execution():
    database = MagicMock()
    database.run.return_value = "[(42,)]"

    validator = MagicMock()
    validator.validate.return_value = ValidationResult(is_valid=True)

    execution_tool = SQLExecutionTool(
        database=database,
        validator=validator,
    )
    langchain_tool = execution_tool.as_langchain_tool()

    result = langchain_tool.invoke(
        {"query": "SELECT COUNT(*) FROM customers"}
    )

    assert result == "[(42,)]"
    validator.validate.assert_called_once_with(
        "SELECT COUNT(*) FROM customers"
    )
    database.run.assert_called_once_with(
        "SELECT COUNT(*) FROM customers"
    )


def test_langchain_tool_does_not_execute_invalid_sql():
    database = MagicMock()

    validator = MagicMock()
    validator.validate.return_value = ValidationResult(
        is_valid=False,
        reason="SQL query must be read-only.",
    )

    execution_tool = SQLExecutionTool(
        database=database,
        validator=validator,
    )
    langchain_tool = execution_tool.as_langchain_tool()

    with pytest.raises(SQLValidationError, match="read-only"):
        langchain_tool.invoke({"query": "DELETE FROM customers"})

    database.run.assert_not_called()


def test_langchain_tool_declares_query_input():
    database = MagicMock()
    validator = MagicMock()

    execution_tool = SQLExecutionTool(
        database=database,
        validator=validator,
    )
    langchain_tool = execution_tool.as_langchain_tool()

    schema = langchain_tool.get_input_schema().model_json_schema()

    assert "query" in schema["properties"]
    assert "query" in schema["required"]