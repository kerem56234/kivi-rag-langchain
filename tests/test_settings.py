# tests/test_settings.py

from dataclasses import FrozenInstanceError

import pytest

from deep_sql_agent.settings import AppSettings


def test_from_env_reads_all_configuration(monkeypatch):
    monkeypatch.setenv(
        "DEEP_SQL_DATABASE_URI",
        "postgresql+psycopg://user:password@localhost:5432/test_db",
    )
    monkeypatch.setenv("DEEP_SQL_OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setenv("DEEP_SQL_OLLAMA_MODEL", "qwen3:8b")
    monkeypatch.setenv("DEEP_SQL_TEMPERATURE", "0.2")

    settings = AppSettings.from_env()

    assert settings.database_uri == (
        "postgresql+psycopg://user:password@localhost:5432/test_db"
    )
    assert settings.ollama_base_url == "http://ollama:11434"
    assert settings.ollama_model == "qwen3:8b"
    assert settings.temperature == 0.2


def test_from_env_uses_optional_defaults(monkeypatch):
    monkeypatch.setenv(
        "DEEP_SQL_DATABASE_URI",
        "postgresql+psycopg://localhost/test_db",
    )
    monkeypatch.delenv("DEEP_SQL_OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("DEEP_SQL_OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("DEEP_SQL_TEMPERATURE", raising=False)

    settings = AppSettings.from_env()

    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_model == "qwen3:latest"
    assert settings.temperature == 0.0


@pytest.mark.parametrize(
    "database_uri",
    ["", " ", "\n\t"],
)
def test_from_env_rejects_missing_or_empty_database_uri(
    monkeypatch,
    database_uri,
):
    monkeypatch.setenv("DEEP_SQL_DATABASE_URI", database_uri)

    with pytest.raises(
        ValueError,
        match="DEEP_SQL_DATABASE_URI must be a non-empty string",
    ):
        AppSettings.from_env()


def test_from_env_rejects_unset_database_uri(monkeypatch):
    monkeypatch.delenv("DEEP_SQL_DATABASE_URI", raising=False)

    with pytest.raises(
        ValueError,
        match="DEEP_SQL_DATABASE_URI must be a non-empty string",
    ):
        AppSettings.from_env()


@pytest.mark.parametrize(
    "temperature",
    [
        "-0.1",
        "2.1",
        "not-a-number",
        "",
    ],
)
def test_from_env_rejects_invalid_temperature(
    monkeypatch,
    temperature,
):
    monkeypatch.setenv(
        "DEEP_SQL_DATABASE_URI",
        "postgresql+psycopg://localhost/test_db",
    )
    monkeypatch.setenv("DEEP_SQL_TEMPERATURE", temperature)

    with pytest.raises(
        ValueError,
        match="DEEP_SQL_TEMPERATURE must be a number between 0 and 2",
    ):
        AppSettings.from_env()


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        (
            "database_uri",
            "",
            "database_uri must be a non-empty string",
        ),
        (
            "ollama_base_url",
            " ",
            "ollama_base_url must be a non-empty string",
        ),
        (
            "ollama_model",
            "",
            "ollama_model must be a non-empty string",
        ),
    ],
)
def test_constructor_rejects_invalid_string_configuration(
    field_name,
    value,
    message,
):
    arguments = {
        "database_uri": "postgresql+psycopg://localhost/test_db",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "qwen3:latest",
        "temperature": 0.0,
    }
    arguments[field_name] = value

    with pytest.raises(ValueError, match=message):
        AppSettings(**arguments)


@pytest.mark.parametrize(
    "temperature",
    [-0.1, 2.1, "0.2", None, True],
)
def test_constructor_rejects_invalid_temperature(temperature):
    with pytest.raises(
        ValueError,
        match="temperature must be a number between 0 and 2",
    ):
        AppSettings(
            database_uri="postgresql+psycopg://localhost/test_db",
            temperature=temperature,
        )


def test_settings_are_immutable():
    settings = AppSettings(
        database_uri="postgresql+psycopg://localhost/test_db"
    )

    with pytest.raises(FrozenInstanceError):
        settings.temperature = 1.0

def test_from_env_reads_include_tables(monkeypatch):
    monkeypatch.setenv(
        "DEEP_SQL_DATABASE_URI",
        "postgresql+psycopg://localhost/test_db",
    )
    monkeypatch.setenv(
        "DEEP_SQL_INCLUDE_TABLES",
        "delivery_orders, delivery_order_items, customer",
    )

    settings = AppSettings.from_env()

    assert settings.include_tables == (
        "delivery_orders",
        "delivery_order_items",
        "customer",
    )


def test_from_env_defaults_include_tables_to_none(monkeypatch):
    monkeypatch.setenv(
        "DEEP_SQL_DATABASE_URI",
        "postgresql+psycopg://localhost/test_db",
    )
    monkeypatch.delenv("DEEP_SQL_INCLUDE_TABLES", raising=False)

    settings = AppSettings.from_env()

    assert settings.include_tables is None


@pytest.mark.parametrize(
    "raw_tables",
    [
        "",
        " ",
        ",",
        "delivery_orders,,customer",
        "delivery-orders",
        "delivery_orders;DROP TABLE customer",
    ],
)
def test_from_env_rejects_invalid_include_tables(
    monkeypatch,
    raw_tables,
):
    monkeypatch.setenv(
        "DEEP_SQL_DATABASE_URI",
        "postgresql+psycopg://localhost/test_db",
    )
    monkeypatch.setenv("DEEP_SQL_INCLUDE_TABLES", raw_tables)

    with pytest.raises(
        ValueError,
        match="DEEP_SQL_INCLUDE_TABLES",
    ):
        AppSettings.from_env()


def test_constructor_accepts_include_tables_tuple():
    settings = AppSettings(
        database_uri="postgresql+psycopg://localhost/test_db",
        include_tables=("delivery_orders", "customer"),
    )

    assert settings.include_tables == (
        "delivery_orders",
        "customer",
    )


@pytest.mark.parametrize(
    "include_tables",
    [
        (),
        [],
        ("",),
        ("delivery-orders",),
        ("customer", 123),
        ("customer", "customer"),
    ],
)
def test_constructor_rejects_invalid_include_tables(include_tables):
    with pytest.raises(
        ValueError,
        match="include_tables",
    ):
        AppSettings(
            database_uri="postgresql+psycopg://localhost/test_db",
            include_tables=include_tables,
        )