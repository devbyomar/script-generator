"""LangGraph agent — the compiled pipeline graph.

Graph flow:
  Fetch → Score → Filter → Cluster → Extract → Outline → Generate → Validate
                                                                       ↓
                                                              (retry if failed)
"""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from src.models.state import AgentState
from src.nodes import (
    credibility_filter_node,
    engagement_scoring_node,
    fetch_tweets_node,
    narrative_extraction_node,
    quality_check_node,
    script_generation_node,
    script_outline_node,
    sentiment_clustering_node,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


# ── Conditional edges ─────────────────────────────────────────

def _should_retry_or_end(state: AgentState) -> str:
    """After quality check, decide whether to retry script generation."""
    if state.get("quality_passed", False):
        return "end"
    retry_count = state.get("retry_count", 0)
    if retry_count >= MAX_RETRIES:
        logger.warning("Max retries reached — accepting script as-is.")
        return "end"
    logger.info("Quality check failed — retrying script (attempt %d)", retry_count + 1)
    return "retry"


def _has_tweets(state: AgentState) -> str:
    """After fetching, check if we got any tweets."""
    if state.get("tweets_raw"):
        return "continue"
    return "abort"


def _increment_retry(state: AgentState) -> dict:
    """Bump the retry counter."""
    return {"retry_count": state.get("retry_count", 0) + 1}


# ── Graph construction ────────────────────────────────────────

def build_graph() -> StateGraph:
    """Construct and return the compiled LangGraph pipeline."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("fetch_tweets", fetch_tweets_node)
    graph.add_node("engagement_scoring", engagement_scoring_node)
    graph.add_node("credibility_filter", credibility_filter_node)
    graph.add_node("sentiment_clustering", sentiment_clustering_node)
    graph.add_node("narrative_extraction", narrative_extraction_node)
    graph.add_node("script_outline", script_outline_node)
    graph.add_node("script_generation", script_generation_node)
    graph.add_node("quality_check", quality_check_node)
    graph.add_node("increment_retry", _increment_retry)

    # Set entry point
    graph.set_entry_point("fetch_tweets")

    # Linear flow with early-abort after fetch
    graph.add_conditional_edges(
        "fetch_tweets",
        _has_tweets,
        {"continue": "engagement_scoring", "abort": END},
    )
    graph.add_edge("engagement_scoring", "credibility_filter")
    graph.add_edge("credibility_filter", "sentiment_clustering")
    graph.add_edge("sentiment_clustering", "narrative_extraction")
    graph.add_edge("narrative_extraction", "script_outline")
    graph.add_edge("script_outline", "script_generation")
    graph.add_edge("script_generation", "quality_check")

    # Retry loop
    graph.add_conditional_edges(
        "quality_check",
        _should_retry_or_end,
        {"end": END, "retry": "increment_retry"},
    )
    graph.add_edge("increment_retry", "script_generation")

    return graph.compile()
