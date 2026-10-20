# tests/test_agent_factory.py

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from deep_sql_agent.agent import SQLAgent
from deep_sql_agent.agent_factory import (
    LangChainAgentAdapter,
    SQLAgentFactory,
)
from deep_sql_agent.exceptions import AgentConfigurationError


# ============================================================
# Test helpers
# ============================================================

def completed_safe_sql_messages(
    *,
    question: str = "How many customers are there?",
    query: str = "SELECT COUNT(*) FROM customers",
    tool_output: str = "[(42,)]",
    final_answer: str = "There are 42 customers.",
):
    """Return a completed safe SQL tool-call message sequence."""
    return [
        HumanMessage(content=question),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "safe_sql_execution",
                    "args": {"query": query},
                    "id": "safe-sql-call-1",
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(
            content=tool_output,
            tool_call_id="safe-sql-call-1",
            name="safe_sql_execution",
        ),
        AIMessage(content=final_answer),
    ]


# ============================================================
# LangChain agent adapter
# ============================================================

def test_adapter_converts_user_question_to_langchain_messages():
    langchain_agent = MagicMock()
    langchain_agent.invoke.return_value = {
        "messages": completed_safe_sql_messages()
    }

    adapter = LangChainAgentAdapter(langchain_agent)

    result = adapter.invoke(
        {"user_question": "How many customers are there?"}
    )

    langchain_agent.invoke.assert_called_once_with(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "How many customers are there?",
                }
            ]
        }
    )
    assert result["output"] == "There are 42 customers."


def test_adapter_preserves_prior_messages_as_intermediate_steps():
    langchain_agent = MagicMock()
    messages = completed_safe_sql_messages(
        question="Question",
        query="SELECT 1",
        tool_output="[(1,)]",
        final_answer="Final answer",
    )
    langchain_agent.invoke.return_value = {"messages": messages}

    adapter = LangChainAgentAdapter(langchain_agent)

    result = adapter.invoke({"user_question": "Question"})

    assert result["intermediate_steps"] == messages[:-1]


def test_adapter_rejects_database_answer_without_safe_sql_execution():
    langchain_agent = MagicMock()
    langchain_agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="Which items sell the most?"),
            AIMessage(
                content=(
                    "Run this SQL: "
                    "SELECT item_id, SUM(quantity) FROM order_items "
                    "GROUP BY item_id"
                )
            ),
        ]
    }
    adapter = LangChainAgentAdapter(langchain_agent)

    with pytest.raises(
        AgentConfigurationError,
        match="without executing safe_sql_execution",
    ):
        adapter.invoke(
            {"user_question": "Which items sell the most?"}
        )


def test_adapter_accepts_completed_safe_sql_execution():
    messages = completed_safe_sql_messages(
        question="Which items sell the most?",
        query=(
            "SELECT item_name, SUM(quantity) AS units_sold "
            "FROM order_items GROUP BY item_name "
            "ORDER BY units_sold DESC"
        ),
        tool_output="[('Item A', 100), ('Item B', 80)]",
        final_answer=(
            "Item A sold 100 units and Item B sold 80 units."
        ),
    )
    langchain_agent = MagicMock()
    langchain_agent.invoke.return_value = {"messages": messages}
    adapter = LangChainAgentAdapter(langchain_agent)

    result = adapter.invoke(
        {"user_question": "Which items sell the most?"}
    )

    assert result["output"] == (
        "Item A sold 100 units and Item B sold 80 units."
    )
    assert result["intermediate_steps"] == messages[:-1]


def test_adapter_rejects_result_from_unrelated_tool():
    langchain_agent = MagicMock()
    langchain_agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="How many customers are there?"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "unrelated_tool",
                        "args": {},
                        "id": "unrelated-call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content="42",
                tool_call_id="unrelated-call-1",
                name="unrelated_tool",
            ),
            AIMessage(content="There are 42 customers."),
        ]
    }
    adapter = LangChainAgentAdapter(langchain_agent)

    with pytest.raises(
        AgentConfigurationError,
        match="without executing safe_sql_execution",
    ):
        adapter.invoke(
            {"user_question": "How many customers are there?"}
        )


def test_adapter_rejects_safe_tool_call_without_tool_result():
    langchain_agent = MagicMock()
    langchain_agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="How many customers are there?"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "safe_sql_execution",
                        "args": {
                            "query": "SELECT COUNT(*) FROM customers"
                        },
                        "id": "safe-sql-call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="There are 42 customers."),
        ]
    }
    adapter = LangChainAgentAdapter(langchain_agent)

    with pytest.raises(
        AgentConfigurationError,
        match="without executing safe_sql_execution",
    ):
        adapter.invoke(
            {"user_question": "How many customers are there?"}
        )


def test_adapter_rejects_tool_result_with_wrong_call_id():
    langchain_agent = MagicMock()
    langchain_agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="How many customers are there?"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "safe_sql_execution",
                        "args": {
                            "query": "SELECT COUNT(*) FROM customers"
                        },
                        "id": "safe-sql-call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content="[(42,)]",
                tool_call_id="different-call-id",
                name="safe_sql_execution",
            ),
            AIMessage(content="There are 42 customers."),
        ]
    }
    adapter = LangChainAgentAdapter(langchain_agent)

    with pytest.raises(
        AgentConfigurationError,
        match="without executing safe_sql_execution",
    ):
        adapter.invoke(
            {"user_question": "How many customers are there?"}
        )


@pytest.mark.parametrize(
    "result",
    [
        None,
        {},
        {"messages": None},
        {"messages": []},
    ],
)
def test_adapter_rejects_malformed_agent_results(result):
    langchain_agent = MagicMock()
    langchain_agent.invoke.return_value = result
    adapter = LangChainAgentAdapter(langchain_agent)

    with pytest.raises(
        AgentConfigurationError,
        match="valid message result",
    ):
        adapter.invoke({"user_question": "Question"})


def test_adapter_rejects_final_message_without_text_content():
    langchain_agent = MagicMock()
    langchain_agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="Question"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "safe_sql_execution",
                        "args": {"query": "SELECT 1"},
                        "id": "safe-sql-call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content="[(1,)]",
                tool_call_id="safe-sql-call-1",
                name="safe_sql_execution",
            ),
            AIMessage(content=""),
        ]
    }
    adapter = LangChainAgentAdapter(langchain_agent)

    with pytest.raises(
        AgentConfigurationError,
        match="valid final answer",
    ):
        adapter.invoke({"user_question": "Question"})


def test_adapter_constructor_rejects_missing_agent():
    with pytest.raises(
        ValueError,
        match="langchain_agent must not be None",
    ):
        LangChainAgentAdapter(None)


# ============================================================
# SQL agent factory
# ============================================================

def test_factory_builds_agent_with_model_tool_and_system_prompt():
    model = MagicMock()

    execution_tool = MagicMock()
    langchain_tool = MagicMock()
    execution_tool.as_langchain_tool.return_value = langchain_tool

    prompt_builder = MagicMock()
    prompt_builder.build_system_prompt.return_value = "System prompt"

    langchain_agent = MagicMock()

    with patch(
        "deep_sql_agent.agent_factory.create_agent",
        return_value=langchain_agent,
    ) as create_agent_mock:
        factory = SQLAgentFactory(
            model=model,
            execution_tool=execution_tool,
            prompt_builder=prompt_builder,
        )

        agent = factory.create(
            schema_context="CREATE TABLE customers (id INTEGER);"
        )

    assert isinstance(agent, SQLAgent)

    prompt_builder.build_system_prompt.assert_called_once_with(
        "CREATE TABLE customers (id INTEGER);"
    )
    execution_tool.as_langchain_tool.assert_called_once_with()
    create_agent_mock.assert_called_once_with(
        model=model,
        tools=[langchain_tool],
        system_prompt="System prompt",
    )


def test_factory_wraps_agent_creation_errors():
    factory = SQLAgentFactory(
        model=MagicMock(),
        execution_tool=MagicMock(),
        prompt_builder=MagicMock(),
    )

    with patch(
        "deep_sql_agent.agent_factory.create_agent",
        side_effect=RuntimeError("agent creation failed"),
    ):
        with pytest.raises(
            AgentConfigurationError,
            match="Failed to create LangChain SQL agent",
        ) as error:
            factory.create("CREATE TABLE customers (id INTEGER);")

    assert isinstance(error.value.__cause__, RuntimeError)


@pytest.mark.parametrize(
    ("argument_name", "arguments"),
    [
        (
            "model",
            {
                "model": None,
                "execution_tool": MagicMock(),
                "prompt_builder": MagicMock(),
            },
        ),
        (
            "execution_tool",
            {
                "model": MagicMock(),
                "execution_tool": None,
                "prompt_builder": MagicMock(),
            },
        ),
        (
            "prompt_builder",
            {
                "model": MagicMock(),
                "execution_tool": MagicMock(),
                "prompt_builder": None,
            },
        ),
    ],
)
def test_factory_rejects_missing_dependency(
    argument_name,
    arguments,
):
    with pytest.raises(
        ValueError,
        match=f"{argument_name} must not be None",
    ):
        SQLAgentFactory(**arguments)