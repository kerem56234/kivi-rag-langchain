# tests/test_logging_config.py

import logging
from unittest.mock import patch

import pytest

from deep_sql_agent.logging_config import (
    configure_logging,
    redact_sensitive_text,
    truncate_log_value,
)


def test_configure_logging_enables_debug_level():
    with (
        patch("deep_sql_agent.logging_config.logging.basicConfig") as basic,
        patch("deep_sql_agent.logging_config.logging.captureWarnings") as capture,
    ):
        configure_logging(debug=True)

    assert basic.call_args.kwargs["level"] == logging.DEBUG
    assert basic.call_args.kwargs["force"] is True
    capture.assert_called_once_with(True)


def test_configure_logging_uses_warning_level_normally():
    with (
        patch("deep_sql_agent.logging_config.logging.basicConfig") as basic,
        patch("deep_sql_agent.logging_config.logging.captureWarnings"),
    ):
        configure_logging(debug=False)

    assert basic.call_args.kwargs["level"] == logging.WARNING


@pytest.mark.parametrize(
    ("text", "secret"),
    [
        (
            "postgresql+psycopg://reader:secret@localhost:5432/database",
            "secret",
        ),
        (
            "DATABASE_URL=postgresql://user:hunter2@db/database",
            "hunter2",
        ),
        (
            "password=do-not-log-this",
            "do-not-log-this",
        ),
        (
            "password: do-not-log-this",
            "do-not-log-this",
        ),
    ],
)
def test_redact_sensitive_text_removes_secrets(text, secret):
    result = redact_sensitive_text(text)

    assert secret not in result
    assert "[REDACTED]" in result


def test_redact_sensitive_text_preserves_safe_text():
    text = "Executing SELECT COUNT(*) FROM customers"

    assert redact_sensitive_text(text) == text


def test_truncate_log_value_preserves_short_values():
    assert truncate_log_value("short result", max_length=20) == "short result"


def test_truncate_log_value_limits_long_values():
    result = truncate_log_value("x" * 100, max_length=20)

    assert len(result) <= 20
    assert result.endswith("...")


def test_truncate_log_value_redacts_before_truncating():
    result = truncate_log_value(
        "password=super-secret-password",
        max_length=100,
    )

    assert "super-secret-password" not in result
    assert "[REDACTED]" in result