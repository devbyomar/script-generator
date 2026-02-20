"""NarrativeExtractionNode — extracts dominant narratives from sentiment clusters."""

from __future__ import annotations

import json
import logging

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.models.narratives import Narrative
from src.models.state import AgentState
from src.prompts.sentiment import CLUSTERING_SYSTEM, CLUSTERING_USER

logger = logging.getLogger(__name__)


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.4,
        max_tokens=4096,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _extract_narratives(llm: ChatOpenAI, tweets_data: list[dict], num_clusters: int) -> list[dict]:
    """Ask the LLM to cluster tweets into dominant narratives."""
    system = CLUSTERING_SYSTEM.format(num_clusters=num_clusters)
    user = CLUSTERING_USER.format(
        count=len(tweets_data),
        tweets_json=json.dumps(tweets_data, indent=2),
        num_clusters=num_clusters,
    )
    response = llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return json.loads(raw)


def narrative_extraction_node(state: AgentState) -> dict:
    """LangGraph node: extract dominant narratives."""
    tweets = state.get("tweets_filtered", [])
    sentiment_data = state.get("sentiment_clusters", [])
    logger.info("📖 NarrativeExtractionNode — extracting from %d tweets …", len(tweets))

    if not tweets:
        return {"dominant_narratives": [], "error": "No tweets for narrative extraction."}

    llm = _build_llm()

    # Build enriched tweet data for the LLM
    sentiment_map = {s["tweet_id"]: s for s in sentiment_data if "tweet_id" in s}
    tweets_enriched = []
    for tw in tweets:
        entry = {
            "tweet_id": tw.id,
            "text": tw.text,
            "engagement_score": tw.engagement_score,
            "credibility_score": tw.credibility_score,
            "author": tw.author.username,
            "verified": tw.author.verified,
        }
        if tw.id in sentiment_map:
            entry.update(sentiment_map[tw.id])
        tweets_enriched.append(entry)

    try:
        raw_narratives = _extract_narratives(
            llm, tweets_enriched, settings.num_narratives
        )
    except Exception as exc:
        logger.exception("Narrative extraction failed")
        return {"dominant_narratives": [], "error": f"Narrative extraction error: {exc}"}

    narratives: list[Narrative] = []
    for i, raw in enumerate(raw_narratives):
        narratives.append(Narrative(
            title=raw.get("title", f"Narrative {i + 1}"),
            summary=raw.get("summary", ""),
            emotion=raw.get("emotion", "neutral"),
            intensity=float(raw.get("intensity", 0.5)),
            stance=raw.get("stance", "divided"),
            supporting_tweet_ids=raw.get("tweet_ids", []),
            key_phrases=raw.get("key_phrases", []),
            counter_arguments=raw.get("counter_arguments", []),
            relevance_score=float(raw.get("relevance_score", 50.0)) if "relevance_score" in raw else float(100 - i * 15),
        ))

    narratives.sort(key=lambda n: n.relevance_score, reverse=True)
    logger.info("✅ Extracted %d narratives", len(narratives))
    return {"dominant_narratives": narratives, "error": ""}
