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
def test_main_enables_debug_logging_when_debug_flag_is_present(capsys):
    service = MagicMock()
    service.answer.return_value = AgentResponse(answer="Debug answer")

    with (
        patch(
            "deep_sql_agent.cli.ApplicationFactory.from_environment",
            return_value=service,
        ),
        patch(
            "deep_sql_agent.cli.configure_logging",
        ) as configure_logging,
    ):
        exit_code = main(["--debug", "Question"])

    assert exit_code == 0
    configure_logging.assert_called_once_with(debug=True)
    service.answer.assert_called_once_with("Question")

    captured = capsys.readouterr()
    assert captured.out.strip() == "Debug answer"


def test_main_configures_normal_logging_without_debug_flag():
    service = MagicMock()
    service.answer.return_value = AgentResponse(answer="Answer")

    with (
        patch(
            "deep_sql_agent.cli.ApplicationFactory.from_environment",
            return_value=service,
        ),
        patch(
            "deep_sql_agent.cli.configure_logging",
        ) as configure_logging,
    ):
        exit_code = main(["Question"])

    assert exit_code == 0
    configure_logging.assert_called_once_with(debug=False)


def test_main_logs_exception_traceback_in_debug_mode(capsys):
    original_error = RuntimeError("underlying LangChain failure")

    with (
        patch(
            "deep_sql_agent.cli.ApplicationFactory.from_environment",
            side_effect=original_error,
        ),
        patch(
            "deep_sql_agent.cli.configure_logging",
        ),
        patch(
            "deep_sql_agent.cli.logger.exception",
        ) as log_exception,
    ):
        exit_code = main(["--debug", "Question"])

    assert exit_code == 1
    log_exception.assert_called_once_with(
        "Application failed while answering the question."
    )

    captured = capsys.readouterr()
    assert "underlying LangChain failure" in captured.err


def test_main_does_not_log_traceback_in_normal_mode(capsys):
    with (
        patch(
            "deep_sql_agent.cli.ApplicationFactory.from_environment",
            side_effect=RuntimeError("application failed"),
        ),
        patch(
            "deep_sql_agent.cli.configure_logging",
        ),
        patch(
            "deep_sql_agent.cli.logger.exception",
        ) as log_exception,
    ):
        exit_code = main(["Question"])

    assert exit_code == 1
    log_exception.assert_not_called()

    captured = capsys.readouterr()
    assert "application failed" in captured.err