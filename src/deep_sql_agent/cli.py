# src/deep_sql_agent/cli.py

from __future__ import annotations

from collections.abc import Sequence

from deep_sql_agent.application import ApplicationFactory


def main(argv: Sequence[str] | None = None) -> int:
    """Run one natural-language database question."""
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())