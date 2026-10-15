# tests/test_agent.py

from unittest.mock import MagicMock

import pytest

from deep_sql_agent.agent import AgentResponse, SQLAgent
from deep_sql_agent.exceptions import AgentExecutionError


def test_answer_invokes_executor_with_user_question():
    executor = MagicMock()
    executor.invoke.return_value = {
        "output": "There are 42 customers.",
        "intermediate_steps": [],
    }
    agent = SQLAgent(executor=executor)

    response = agent.answer("How many customers are there?")

    executor.invoke.assert_called_once_with(
        {"user_question": "How many customers are there?"}
    )
    assert response == AgentResponse(
        answer="There are 42 customers.",
        intermediate_steps=[],
        success=True,
        error_message="",
    )


def test_answer_preserves_intermediate_steps():
    steps = [
        (
            MagicMock(tool="safe_sql_execution"),
            "[(42,)]",
        )
    ]
    executor = MagicMock()
    executor.invoke.return_value = {
        "output": "There are 42 customers.",
        "intermediate_steps": steps,
    }
    agent = SQLAgent(executor=executor)

    response = agent.answer("How many customers are there?")

    assert response.intermediate_steps == steps


def test_answer_defaults_to_empty_intermediate_steps():
    executor = MagicMock()
    executor.invoke.return_value = {
        "output": "No customers were found.",
    }
    agent = SQLAgent(executor=executor)

    response = agent.answer("Are there any customers?")

    assert response.intermediate_steps == []


@pytest.mark.parametrize(
    "question",
    [
        "",
        " ",
        "\n\t",
        None,
        123,
        [],
        {},
    ],
)
def test_answer_rejects_invalid_question(question):
    executor = MagicMock()
    agent = SQLAgent(executor=executor)

    with pytest.raises(
        ValueError,
        match="question must be a non-empty string",
    ):
        agent.answer(question)

    executor.invoke.assert_not_called()


def test_answer_wraps_executor_errors():
    executor = MagicMock()
    original_error = RuntimeError("model unavailable")
    executor.invoke.side_effect = original_error
    agent = SQLAgent(executor=executor)

    with pytest.raises(
        AgentExecutionError,
        match="SQL agent failed to produce an answer",
    ) as error:
        agent.answer("How many customers are there?")

    assert error.value.__cause__ is original_error


@pytest.mark.parametrize(
    "result",
    [
        None,
        {},
        {"output": None},
        {"output": 42},
        {"output": ""},
        {"output": "   "},
    ],
)
def test_answer_rejects_malformed_executor_result(result):
    executor = MagicMock()
    executor.invoke.return_value = result
    agent = SQLAgent(executor=executor)

    with pytest.raises(
        AgentExecutionError,
        match="valid output",
    ):
        agent.answer("How many customers are there?")


def test_constructor_rejects_missing_executor():
    with pytest.raises(ValueError, match="executor must not be None"):
        SQLAgent(executor=None)