"""LangGraph agent state schema."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from src.models.tweets import Tweet
from src.models.narratives import Narrative
from src.models.script import ScriptOutline, FinalScript


def _replace(old: list, new: list) -> list:  # noqa: ARG001
    """Reducer that always replaces the old value."""
    return new


class AgentState(TypedDict):
    """Full state flowing through the LangGraph pipeline."""

    # ── Raw data ──────────────────────────────────────────
    tweets_raw: Annotated[list[Tweet], _replace]

    # ── After engagement scoring ──────────────────────────
    tweets_scored: Annotated[list[Tweet], _replace]

    # ── After credibility filtering ───────────────────────
    tweets_filtered: Annotated[list[Tweet], _replace]

    # ── Sentiment + clustering ────────────────────────────
    sentiment_clusters: Annotated[list[dict], _replace]

    # ── Narrative extraction ──────────────────────────────
    dominant_narratives: Annotated[list[Narrative], _replace]

    # ── Script stages ─────────────────────────────────────
    script_outline: Annotated[ScriptOutline | None, lambda _o, n: n]
    final_script: Annotated[FinalScript | None, lambda _o, n: n]

    # ── Quality gate ──────────────────────────────────────
    quality_passed: Annotated[bool, lambda _o, n: n]
    quality_feedback: Annotated[str, lambda _o, n: n]

    # ── LLM message log (for debugging) ──────────────────
    messages: Annotated[list[BaseMessage], add_messages]

    # ── Metadata ──────────────────────────────────────────
    error: Annotated[str, lambda _o, n: n]
    retry_count: Annotated[int, lambda _o, n: n]
