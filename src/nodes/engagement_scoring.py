"""EngagementScoringNode — applies weighted engagement scoring."""

from __future__ import annotations

import logging

from src.config import settings
from src.models.state import AgentState
from src.scoring.engagement import score_tweets

logger = logging.getLogger(__name__)


def engagement_scoring_node(state: AgentState) -> dict:
    """LangGraph node: score tweets by engagement."""
    raw = state.get("tweets_raw", [])
    logger.info("📊 EngagementScoringNode — scoring %d tweets …", len(raw))

    if not raw:
        return {"tweets_scored": [], "error": "No raw tweets to score."}

    scored = score_tweets(raw)

    # Apply minimum threshold
    filtered = [t for t in scored if t.engagement_score >= settings.min_engagement_score]
    logger.info(
        "✅ %d tweets passed engagement threshold (%.1f)",
        len(filtered), settings.min_engagement_score,
    )

    if not filtered:
        # Fallback: keep top 50 even if below threshold
        filtered = scored[:50]
        logger.warning("⚠️  Low-signal fallback: keeping top %d tweets", len(filtered))

    return {"tweets_scored": filtered, "error": ""}
