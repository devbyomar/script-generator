"""Logging setup."""

from __future__ import annotations

import logging
import sys

from rich.logging import RichHandler


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging with Rich."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )
    # Silence noisy libraries
    for name in ("httpx", "httpcore", "openai", "tweepy"):
        logging.getLogger(name).setLevel(logging.WARNING)
