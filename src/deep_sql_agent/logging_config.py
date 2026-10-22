# src/deep_sql_agent/logging_config.py

from __future__ import annotations

import logging
import re
import sys
from typing import Any


_DATABASE_URL_PATTERN = re.compile(
    r"(?P<prefix>[a-zA-Z][a-zA-Z0-9+.-]*://"
    r"[^:/@\s]+:)"
    r"(?P<secret>[^@\s]+)"
    r"(?P<suffix>@)",
)

_PASSWORD_PATTERN = re.compile(
    r"(?P<prefix>\bpassword\s*(?:=|:)\s*)"
    r"(?P<secret>[^\s,;]+)",
    re.IGNORECASE,
)


def configure_logging(debug: bool = False) -> None:
    """Configure application logging and warning capture."""
    level = logging.DEBUG if debug else logging.WARNING

    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ),
        stream=sys.stderr,
        force=True,
    )

    # Route warnings, including SQLAlchemy warnings, through logging.
    logging.captureWarnings(True)

    dependency_level = logging.INFO if debug else logging.WARNING

    for logger_name in (
        "httpcore",
        "httpx",
        "urllib3",
    ):
        logging.getLogger(logger_name).setLevel(dependency_level)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)

def redact_sensitive_text(value: Any) -> str:
    """Return a string with common credential formats redacted."""
    text = str(value)

    text = _DATABASE_URL_PATTERN.sub(
        lambda match: (
            f"{match.group('prefix')}[REDACTED]"
            f"{match.group('suffix')}"
        ),
        text,
    )

    text = _PASSWORD_PATTERN.sub(
        lambda match: (
            f"{match.group('prefix')}[REDACTED]"
        ),
        text,
    )

    return text


def truncate_log_value(
    value: Any,
    *,
    max_length: int = 500,
) -> str:
    """Redact and truncate a value before writing it to logs."""
    if not isinstance(max_length, int) or isinstance(max_length, bool):
        raise ValueError("max_length must be a positive integer.")

    if max_length <= 0:
        raise ValueError("max_length must be a positive integer.")

    safe_value = redact_sensitive_text(value)

    if len(safe_value) <= max_length:
        return safe_value

    if max_length <= 3:
        return "." * max_length

    return f"{safe_value[:max_length - 3]}..."