# tests/test_service.py

from unittest.mock import MagicMock, patch

import pytest

from deep_sql_agent.agent import AgentResponse
from deep_sql_agent.service import AgentService


@pytest.fixture
def dependencies():
    database = MagicMock()

    database_connector = MagicMock()
    database_connector.create_sql_database.return_value = database

    model = MagicMock()
    model_factory = MagicMock()
    model_factory.create_chat_model.return_value = model

    validator = MagicMock()
    prompt_builder = MagicMock()

    return {
        "database": database,
        "database_connector": database_connector,
        "model": model,
        "model_factory": model_factory,
        "validator": validator,
        "prompt_builder": prompt_builder,
    }


def test_build_agent_assembles_all_components(dependencies):
    schema_provider = MagicMock()
    schema_provider.get_schema_context.return_value = (
        "CREATE TABLE customers (id INTEGER);"
    )

    execution_tool = MagicMock()
    sql_agent = MagicMock()

    agent_factory = MagicMock()
    agent_factory.create.return_value = sql_agent

    with (
        patch(
            "deep_sql_agent.service.SQLSchemaProvider",
            return_value=schema_provider,
        ) as schema_provider_class,
        patch(
            "deep_sql_agent.service.SQLExecutionTool",
            return_value=execution_tool,
        ) as execution_tool_class,
        patch(
            "deep_sql_agent.service.SQLAgentFactory",
            return_value=agent_factory,
        ) as agent_factory_class,
    ):
        service = AgentService(
            database_connector=dependencies["database_connector"],
            model_factory=dependencies["model_factory"],
            validator=dependencies["validator"],
            prompt_builder=dependencies["prompt_builder"],
        )

        result = service.build_agent()

    assert result is sql_agent

    dependencies[
        "database_connector"
    ].create_sql_database.assert_called_once_with()

    dependencies[
        "model_factory"
    ].create_chat_model.assert_called_once_with()

    schema_provider_class.assert_called_once_with(
        dependencies["database"]
    )
    schema_provider.get_schema_context.assert_called_once_with()

    execution_tool_class.assert_called_once_with(
        database=dependencies["database"],
        validator=dependencies["validator"],
    )

    agent_factory_class.assert_called_once_with(
        model=dependencies["model"],
        execution_tool=execution_tool,
        prompt_builder=dependencies["prompt_builder"],
    )

    agent_factory.create.assert_called_once_with(
        "CREATE TABLE customers (id INTEGER);"
    )


def test_answer_builds_agent_and_delegates_question(dependencies):
    expected_response = AgentResponse(
        answer="There are 42 customers.",
    )

    sql_agent = MagicMock()
    sql_agent.answer.return_value = expected_response

    service = AgentService(
        database_connector=dependencies["database_connector"],
        model_factory=dependencies["model_factory"],
        validator=dependencies["validator"],
        prompt_builder=dependencies["prompt_builder"],
    )

    with patch.object(
        service,
        "build_agent",
        return_value=sql_agent,
    ) as build_agent:
        response = service.answer(
            "How many customers are there?"
        )

    assert response == expected_response
    build_agent.assert_called_once_with()
    sql_agent.answer.assert_called_once_with(
        "How many customers are there?"
    )


def test_answer_reuses_built_agent(dependencies):
    sql_agent = MagicMock()
    sql_agent.answer.side_effect = [
        AgentResponse(answer="First answer"),
        AgentResponse(answer="Second answer"),
    ]

    service = AgentService(
        database_connector=dependencies["database_connector"],
        model_factory=dependencies["model_factory"],
        validator=dependencies["validator"],
        prompt_builder=dependencies["prompt_builder"],
    )

    with patch.object(
        service,
        "build_agent",
        return_value=sql_agent,
    ) as build_agent:
        first = service.answer("First question")
        second = service.answer("Second question")

    assert first.answer == "First answer"
    assert second.answer == "Second answer"
    build_agent.assert_called_once_with()


@pytest.mark.parametrize(
    ("missing_name", "arguments"),
    [
        (
            "database_connector",
            {
                "database_connector": None,
                "model_factory": MagicMock(),
                "validator": MagicMock(),
                "prompt_builder": MagicMock(),
            },
        ),
        (
            "model_factory",
            {
                "database_connector": MagicMock(),
                "model_factory": None,
                "validator": MagicMock(),
                "prompt_builder": MagicMock(),
            },
        ),
        (
            "validator",
            {
                "database_connector": MagicMock(),
                "model_factory": MagicMock(),
                "validator": None,
                "prompt_builder": MagicMock(),
            },
        ),
        (
            "prompt_builder",
            {
                "database_connector": MagicMock(),
                "model_factory": MagicMock(),
                "validator": MagicMock(),
                "prompt_builder": None,
            },
        ),
    ],
)
def test_constructor_rejects_missing_dependency(
    missing_name,
    arguments,
):
    with pytest.raises(
        ValueError,
        match=f"{missing_name} must not be None",
    ):
        AgentService(**arguments)