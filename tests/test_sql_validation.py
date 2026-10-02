# tests/test_sql_validation.py

import pytest

from deep_sql_agent.exceptions import SQLValidationError
from deep_sql_agent.sql_validation import SQLQueryValidator, ValidationResult


# ============================================================
# ValidationResult
# ============================================================

def test_validation_result_defaults_to_empty_reason():
    result = ValidationResult(is_valid=True)

    assert result.is_valid is True
    assert result.reason == ""


# ============================================================
# Valid read-only SQL
# ============================================================

@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM customers",
        "SELECT id, name FROM customers WHERE id = 1",
        "select count(*) from orders",
        "WITH recent_orders AS (SELECT * FROM orders) SELECT * FROM recent_orders",
        "  SELECT * FROM products;  ",
    ],
)
def test_validate_accepts_read_only_queries(query):
    validator = SQLQueryValidator(read_only=True)

    result = validator.validate(query)

    assert result == ValidationResult(is_valid=True, reason="")


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM customers",
        "select count(*) from orders",
        "WITH x AS (SELECT 1) SELECT * FROM x",
    ],
)
def test_is_read_only_returns_true_for_select_queries(query):
    validator = SQLQueryValidator(read_only=True)

    assert validator.is_read_only(query) is True


# ============================================================
# Invalid input
# ============================================================

@pytest.mark.parametrize(
    "query",
    [
        "",
        " ",
        "\n\t",
    ],
)
def test_validate_rejects_empty_or_whitespace_query(query):
    validator = SQLQueryValidator(read_only=True)

    result = validator.validate(query)

    assert result.is_valid is False
    assert "non-empty" in result.reason.lower()


@pytest.mark.parametrize(
    "query",
    [
        None,
        123,
        1.5,
        [],
        {},
    ],
)
def test_validate_rejects_non_string_query(query):
    validator = SQLQueryValidator(read_only=True)

    result = validator.validate(query)

    assert result.is_valid is False
    assert "string" in result.reason.lower()


# ============================================================
# Dangerous or non-read-only SQL
# ============================================================

@pytest.mark.parametrize(
    "query",
    [
        "INSERT INTO customers(name) VALUES ('Alice')",
        "UPDATE customers SET name = 'Alice' WHERE id = 1",
        "DELETE FROM customers WHERE id = 1",
        "DROP TABLE customers",
        "ALTER TABLE customers ADD COLUMN age int",
        "TRUNCATE TABLE customers",
        "CREATE TABLE test_table(id int)",
        "GRANT SELECT ON customers TO public",
        "REVOKE SELECT ON customers FROM public",
    ],
)
def test_validate_rejects_write_or_schema_changing_queries_in_read_only_mode(query):
    validator = SQLQueryValidator(read_only=True)

    result = validator.validate(query)

    assert result.is_valid is False
    assert "read-only" in result.reason.lower()


@pytest.mark.parametrize(
    "query",
    [
        "INSERT INTO customers(name) VALUES ('Alice')",
        "UPDATE customers SET name = 'Alice' WHERE id = 1",
        "DELETE FROM customers WHERE id = 1",
        "DROP TABLE customers",
    ],
)
def test_is_read_only_returns_false_for_non_read_only_queries(query):
    validator = SQLQueryValidator(read_only=True)

    assert validator.is_read_only(query) is False


# ============================================================
# Multiple statements
# ============================================================

@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM customers; DROP TABLE customers;",
        "SELECT 1; SELECT 2;",
        "SELECT * FROM orders; DELETE FROM orders;",
    ],
)
def test_validate_rejects_multiple_statements(query):
    validator = SQLQueryValidator(read_only=True)

    result = validator.validate(query)

    assert result.is_valid is False
    assert "multiple" in result.reason.lower()


# ============================================================
# Exception helper
# ============================================================

def test_reject_dangerous_sql_does_not_raise_for_valid_query():
    validator = SQLQueryValidator(read_only=True)

    validator.reject_dangerous_sql("SELECT * FROM customers")


def test_reject_dangerous_sql_raises_sql_validation_error_for_invalid_query():
    validator = SQLQueryValidator(read_only=True)

    with pytest.raises(SQLValidationError, match="read-only"):
        validator.reject_dangerous_sql("DROP TABLE customers")