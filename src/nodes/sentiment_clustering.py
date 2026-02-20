"""SentimentClusteringNode — analyses sentiment and clusters tweets."""

from __future__ import annotations

import json
import logging

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.models.state import AgentState
from src.prompts.sentiment import SENTIMENT_SYSTEM, SENTIMENT_USER

logger = logging.getLogger(__name__)


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.3,
        max_tokens=4096,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _analyse_batch(llm: ChatOpenAI, tweets_data: list[dict]) -> list[dict]:
    """Send a batch of tweets to the LLM for sentiment analysis."""
    prompt_text = SENTIMENT_USER.format(
        count=len(tweets_data),
        tweets_json=json.dumps(tweets_data, indent=2),
    )
    response = llm.invoke([
        {"role": "system", "content": SENTIMENT_SYSTEM},
        {"role": "user", "content": prompt_text},
    ])
    raw = response.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return json.loads(raw)


def sentiment_clustering_node(state: AgentState) -> dict:
    """LangGraph node: run sentiment analysis on filtered tweets."""
    tweets = state.get("tweets_filtered", [])
    logger.info("🧠 SentimentClusteringNode — analysing %d tweets …", len(tweets))

    if not tweets:
        return {"sentiment_clusters": [], "error": "No tweets for sentiment analysis."}

    llm = _build_llm()

    # Prepare minimal tweet dicts for the LLM
    tweets_for_llm = [
        {"tweet_id": t.id, "text": t.text, "engagement_score": t.engagement_score}
        for t in tweets
    ]

    # Batch in groups of 30 to stay within context window
    batch_size = 30
    all_results: list[dict] = []

    for i in range(0, len(tweets_for_llm), batch_size):
        batch = tweets_for_llm[i : i + batch_size]
        try:
            results = _analyse_batch(llm, batch)
            all_results.extend(results)
        except Exception as exc:
            logger.error("Sentiment batch %d failed: %s", i // batch_size, exc)

    # Map results back to Tweet objects
    result_map = {r["tweet_id"]: r for r in all_results if "tweet_id" in r}
    for tw in tweets:
        if tw.id in result_map:
            r = result_map[tw.id]
            tw.sentiment_label = r.get("sentiment", "neutral")
            tw.sentiment_intensity = float(r.get("intensity", 0.0))

    logger.info("✅ Sentiment analysed for %d / %d tweets", len(result_map), len(tweets))
    return {"sentiment_clusters": all_results, "tweets_filtered": tweets, "error": ""}
