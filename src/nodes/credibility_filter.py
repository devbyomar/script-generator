"""CredibilityFilterNode — filters tweets by author credibility."""

from __future__ import annotations

import logging

from src.config import settings
from src.models.state import AgentState
from src.scoring.credibility import score_credibility

logger = logging.getLogger(__name__)


def credibility_filter_node(state: AgentState) -> dict:
    """LangGraph node: filter tweets by credibility score."""
    scored = state.get("tweets_scored", [])
    logger.info("🛡️  CredibilityFilterNode — filtering %d tweets …", len(scored))

    if not scored:
        return {"tweets_filtered": [], "error": "No scored tweets to filter."}

    filtered = score_credibility(scored, min_score=settings.min_credibility_score)

    if not filtered:
        # Fallback: keep top 30 by credibility regardless of threshold
        all_scored = score_credibility(scored, min_score=0)
        filtered = all_scored[:30]
        logger.warning("⚠️  Low-credibility fallback: keeping top %d tweets", len(filtered))

    logger.info("✅ %d tweets passed credibility filter", len(filtered))
    return {"tweets_filtered": filtered, "error": ""}
