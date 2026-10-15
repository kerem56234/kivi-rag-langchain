# tests/test_application.py

from unittest.mock import MagicMock, patch

import pytest

from deep_sql_agent.application import ApplicationFactory
from deep_sql_agent.settings import AppSettings


@pytest.fixture
def settings():
    return AppSettings(
        database_uri=(
            "postgresql+psycopg://"
            "user:password@localhost:5432/test_db"
        ),
        ollama_base_url="http://ollama.test:11434",
        ollama_model="qwen3:8b",
        temperature=0.2,
    )


def test_create_service_builds_dependencies_from_settings(settings):
    database_connector = MagicMock()
    model_factory = MagicMock()
    validator = MagicMock()
    prompt_builder = MagicMock()
    service = MagicMock()

    with (
        patch(
            "deep_sql_agent.application.DatabaseConnector",
            return_value=database_connector,
        ) as database_connector_class,
        patch(
            "deep_sql_agent.application.OllamaModelFactory",
            return_value=model_factory,
        ) as model_factory_class,
        patch(
            "deep_sql_agent.application.SQLQueryValidator",
            return_value=validator,
        ) as validator_class,
        patch(
            "deep_sql_agent.application.AgentPromptBuilder",
            return_value=prompt_builder,
        ) as prompt_builder_class,
        patch(
            "deep_sql_agent.application.AgentService",
            return_value=service,
        ) as service_class,
    ):
        result = ApplicationFactory.create_service(settings)

    assert result is service

    database_connector_class.assert_called_once_with(
        database_uri=settings.database_uri,
    )
    model_factory_class.assert_called_once_with(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.temperature,
    )
    validator_class.assert_called_once_with(read_only=True)
    prompt_builder_class.assert_called_once_with()

    service_class.assert_called_once_with(
        database_connector=database_connector,
        model_factory=model_factory,
        validator=validator,
        prompt_builder=prompt_builder,
    )


def test_create_service_rejects_missing_settings():
    with pytest.raises(
        ValueError,
        match="settings must not be None",
    ):
        ApplicationFactory.create_service(None)


def test_from_environment_loads_settings_and_creates_service():
    settings = MagicMock()
    service = MagicMock()

    with (
        patch(
            "deep_sql_agent.application.AppSettings.from_env",
            return_value=settings,
        ) as from_env,
        patch.object(
            ApplicationFactory,
            "create_service",
            return_value=service,
        ) as create_service,
    ):
        result = ApplicationFactory.from_environment()

    assert result is service
    from_env.assert_called_once_with()
    create_service.assert_called_once_with(settings)