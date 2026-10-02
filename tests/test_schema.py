# tests/test_schema.py

from unittest.mock import MagicMock

import pytest

from deep_sql_agent.schema import SQLSchemaProvider


def test_get_table_names_returns_database_table_names():
    database = MagicMock()
    database.get_usable_table_names.return_value = ["customers", "orders"]

    provider = SQLSchemaProvider(database)

    result = provider.get_table_names()

    assert result == ["customers", "orders"]
    database.get_usable_table_names.assert_called_once_with()


def test_get_schema_context_returns_database_table_info_for_all_tables():
    database = MagicMock()
    database.get_table_info.return_value = "CREATE TABLE customers ..."

    provider = SQLSchemaProvider(database)

    result = provider.get_schema_context()

    assert result == "CREATE TABLE customers ..."
    database.get_table_info.assert_called_once_with()


def test_get_table_info_returns_database_table_info_for_specific_tables():
    database = MagicMock()
    database.get_table_info.return_value = "CREATE TABLE orders ..."

    provider = SQLSchemaProvider(database)

    result = provider.get_table_info(["orders"])

    assert result == "CREATE TABLE orders ..."
    database.get_table_info.assert_called_once_with(["orders"])


def test_get_table_info_rejects_empty_table_list():
    database = MagicMock()
    provider = SQLSchemaProvider(database)

    with pytest.raises(ValueError, match="table_names must not be empty"):
        provider.get_table_info([])

    database.get_table_info.assert_not_called()


@pytest.mark.parametrize(
    "table_names",
    [
        None,
        "customers",
        123,
        {},
    ],
)
def test_get_table_info_rejects_invalid_table_names_container(table_names):
    database = MagicMock()
    provider = SQLSchemaProvider(database)

    with pytest.raises(ValueError, match="table_names must be a list"):
        provider.get_table_info(table_names)

    database.get_table_info.assert_not_called()


@pytest.mark.parametrize(
    "table_names",
    [
        [""],
        [" "],
        ["customers", ""],
        ["customers", 123],
        ["customers", None],
    ],
)
def test_get_table_info_rejects_invalid_table_name_values(table_names):
    database = MagicMock()
    provider = SQLSchemaProvider(database)

    with pytest.raises(ValueError, match="Each table name must be a non-empty string"):
        provider.get_table_info(table_names)

    database.get_table_info.assert_not_called()


def test_constructor_rejects_missing_database():
    with pytest.raises(ValueError, match="database must not be None"):
        SQLSchemaProvider(None)