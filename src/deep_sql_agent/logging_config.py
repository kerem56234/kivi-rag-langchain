from __future__ import annotations

import logging
import sys


def configure_logging(debug: bool = False) -> None:
    """Configure application logging for normal or debug operation."""
    level = logging.DEBUG if debug else logging.WARNING

    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ),
        stream=sys.stderr,
        force=True,
    )

    # Keep noisy dependencies at a useful level during application debugging.
    logging.getLogger("httpcore").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.INFO)