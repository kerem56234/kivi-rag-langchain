# src/deep_sql_agent/cli.py

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from deep_sql_agent.application import ApplicationFactory


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="deep-sql-agent",
        description=(
            "Ask a natural-language question about the configured database."
        ),
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
    question = " ".join(arguments.question)

    try:
        service = ApplicationFactory.from_environment()
        response = service.answer(question)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(response.answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())