# tests/test_cli.py

from unittest.mock import MagicMock, patch

import pytest

from deep_sql_agent.agent import AgentResponse
from deep_sql_agent.cli import main


def test_main_builds_service_and_prints_answer(capsys):
    service = MagicMock()
    service.answer.return_value = AgentResponse(
        answer="There are 42 customers."
    )

    with patch(
        "deep_sql_agent.cli.ApplicationFactory.from_environment",
        return_value=service,
    ) as from_environment:
        exit_code = main(
            ["How many customers are there?"]
        )

    assert exit_code == 0
    from_environment.assert_called_once_with()
    service.answer.assert_called_once_with(
        "How many customers are there?"
    )

    captured = capsys.readouterr()
    assert captured.out.strip() == "There are 42 customers."
    assert captured.err == ""


def test_main_supports_questions_containing_multiple_arguments(capsys):
    service = MagicMock()
    service.answer.return_value = AgentResponse(
        answer="Alice has 3 orders."
    )

    with patch(
        "deep_sql_agent.cli.ApplicationFactory.from_environment",
        return_value=service,
    ):
        exit_code = main(
            ["How", "many", "orders", "does", "Alice", "have?"]
        )

    assert exit_code == 0
    service.answer.assert_called_once_with(
        "How many orders does Alice have?"
    )

    captured = capsys.readouterr()
    assert captured.out.strip() == "Alice has 3 orders."


def test_main_returns_error_code_when_application_fails(capsys):
    with patch(
        "deep_sql_agent.cli.ApplicationFactory.from_environment",
        side_effect=RuntimeError("configuration failed"),
    ):
        exit_code = main(["Question"])

    assert exit_code == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "configuration failed" in captured.err


def test_main_returns_error_code_when_agent_fails(capsys):
    service = MagicMock()
    service.answer.side_effect = RuntimeError("agent failed")

    with patch(
        "deep_sql_agent.cli.ApplicationFactory.from_environment",
        return_value=service,
    ):
        exit_code = main(["Question"])

    assert exit_code == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "agent failed" in captured.err


def test_main_requires_a_question():
    with pytest.raises(SystemExit) as error:
        main([])

    assert error.value.code == 2