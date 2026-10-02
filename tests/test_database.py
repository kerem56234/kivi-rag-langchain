# tests/test_database.py

from unittest.mock import MagicMock, patch

import pytest

from deep_sql_agent.database import DatabaseConnector
from deep_sql_agent.exceptions import DatabaseError


def test_create_sql_database_uses_langchain_sql_database_from_uri():
    with patch("deep_sql_agent.database.SQLDatabase") as sql_database_class:
        fake_database = MagicMock()
        sql_database_class.from_uri.return_value = fake_database

        connector = DatabaseConnector(
            database_uri="postgresql+psycopg://user:password@localhost:5432/test_db"
        )

        database = connector.create_sql_database()

        assert database is fake_database
        sql_database_class.from_uri.assert_called_once_with(
            "postgresql+psycopg://user:password@localhost:5432/test_db"
        )


@pytest.mark.parametrize(
    "database_uri",
    [
        "",
        " ",
        "\n\t",
    ],
)
def test_constructor_rejects_empty_database_uri(database_uri):
    with pytest.raises(ValueError, match="database_uri must be a non-empty string"):
        DatabaseConnector(database_uri=database_uri)


@pytest.mark.parametrize(
    "database_uri",
    [
        None,
        123,
        1.5,
        [],
        {},
    ],
)
def test_constructor_rejects_non_string_database_uri(database_uri):
    with pytest.raises(ValueError, match="database_uri must be a non-empty string"):
        DatabaseConnector(database_uri=database_uri)


def test_create_sql_database_wraps_connection_errors():
    with patch("deep_sql_agent.database.SQLDatabase") as sql_database_class:
        original_error = RuntimeError("connection failed")
        sql_database_class.from_uri.side_effect = original_error

        connector = DatabaseConnector(
            database_uri="postgresql+psycopg://user:password@localhost:5432/test_db"
        )

        with pytest.raises(
            DatabaseError,
            match="Failed to create LangChain SQLDatabase",
        ) as error:
            connector.create_sql_database()

        assert error.value.__cause__ is original_error


def test_test_connection_returns_true_when_select_one_succeeds():
    fake_database = MagicMock()
    fake_database.run.return_value = "1"

    connector = DatabaseConnector(
        database_uri="postgresql+psycopg://user:password@localhost:5432/test_db"
    )

    result = connector.test_connection(fake_database)

    assert result is True
    fake_database.run.assert_called_once_with("SELECT 1")


def test_test_connection_returns_false_when_select_one_fails():
    fake_database = MagicMock()
    fake_database.run.side_effect = RuntimeError("database unavailable")

    connector = DatabaseConnector(
        database_uri="postgresql+psycopg://user:password@localhost:5432/test_db"
    )

    result = connector.test_connection(fake_database)

    assert result is False
    fake_database.run.assert_called_once_with("SELECT 1")