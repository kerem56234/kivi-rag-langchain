# src/deep_sql_agent/cli.py

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from deep_sql_agent.application import ApplicationFactory
from deep_sql_agent.logging_config import configure_logging


logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="deep-sql-agent",
        description=(
            "Ask a natural-language question about the configured database."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed diagnostic logging and tracebacks.",
    )
    parser.add_argument(
        "question",
        nargs="+",
        help="Natural-language database question.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one natural-language database question."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    configure_logging(debug=arguments.debug)

    question = " ".join(arguments.question)

    try:
        service = ApplicationFactory.from_environment()
        response = service.answer(question)
    except Exception as exc:
        if arguments.debug:
            logger.exception(
                "Application failed while answering the question."
            )

        print(str(exc), file=sys.stderr)
        return 1

    print(response.answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())