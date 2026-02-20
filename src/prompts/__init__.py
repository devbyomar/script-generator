"""Prompt templates package."""

from src.prompts.sentiment import (
    SENTIMENT_SYSTEM,
    SENTIMENT_USER,
    CLUSTERING_SYSTEM,
    CLUSTERING_USER,
)
from src.prompts.script import (
    OUTLINE_SYSTEM,
    OUTLINE_USER,
    SCRIPT_SYSTEM,
    SCRIPT_USER,
    QUALITY_SYSTEM,
    QUALITY_USER,
)

__all__ = [
    "CLUSTERING_SYSTEM",
    "CLUSTERING_USER",
    "OUTLINE_SYSTEM",
    "OUTLINE_USER",
    "QUALITY_SYSTEM",
    "QUALITY_USER",
    "SCRIPT_SYSTEM",
    "SCRIPT_USER",
    "SENTIMENT_SYSTEM",
    "SENTIMENT_USER",
]
