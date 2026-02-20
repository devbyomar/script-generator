"""FetchTweetsNode — pulls NFL tweets from X API v2 recent search."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import tweepy

from src.config import settings
from src.models.state import AgentState
from src.models.tweets import Tweet, TweetAuthor, TweetMetrics
from src.utils.nfl import build_search_queries

logger = logging.getLogger(__name__)

# Fields we request from the X API v2
TWEET_FIELDS = [
    "created_at", "public_metrics", "conversation_id",
    "context_annotations", "referenced_tweets",
]
USER_FIELDS = [
    "created_at", "public_metrics", "verified", "description",
]
EXPANSIONS = ["author_id", "referenced_tweets.id"]


def _build_client() -> tweepy.Client:
    """Create an authenticated X API v2 client."""
    return tweepy.Client(
        bearer_token=settings.x_bearer_token,
        wait_on_rate_limit=True,
    )


def _parse_tweet(tweet_data, users_map: dict) -> Tweet:
    """Convert a tweepy tweet + user lookup into our internal Tweet model."""
    author_data = users_map.get(tweet_data.author_id)
    pm = tweet_data.public_metrics or {}
    author_pm = getattr(author_data, "public_metrics", {}) or {}

    author = TweetAuthor(
        id=str(tweet_data.author_id),
        username=getattr(author_data, "username", "unknown"),
        name=getattr(author_data, "name", "Unknown"),
        followers_count=author_pm.get("followers_count", 0),
        following_count=author_pm.get("following_count", 0),
        tweet_count=author_pm.get("tweet_count", 0),
        verified=getattr(author_data, "verified", False),
        description=getattr(author_data, "description", "") or "",
        created_at=getattr(author_data, "created_at", None),
    )

    ref_ids: list[str] = []
    if tweet_data.referenced_tweets:
        ref_ids = [str(r.id) for r in tweet_data.referenced_tweets]

    ctx: list[str] = []
    if tweet_data.context_annotations:
        for ann in tweet_data.context_annotations:
            entity = ann.get("entity", {})
            if entity.get("name"):
                ctx.append(entity["name"])

    return Tweet(
        id=str(tweet_data.id),
        text=tweet_data.text,
        created_at=tweet_data.created_at or datetime.utcnow(),
        author=author,
        metrics=TweetMetrics(
            likes=pm.get("like_count", 0),
            retweets=pm.get("retweet_count", 0),
            quote_tweets=pm.get("quote_count", 0),
            replies=pm.get("reply_count", 0),
        ),
        conversation_id=str(tweet_data.conversation_id) if tweet_data.conversation_id else None,
        referenced_tweet_ids=ref_ids,
        context_annotations=ctx,
    )


def fetch_tweets_node(state: AgentState) -> dict:
    """LangGraph node: fetch recent NFL tweets from X API."""
    # If tweets are pre-populated (e.g. dry-run mode), skip API call
    existing = state.get("tweets_raw", [])
    if existing:
        logger.info("🔍 FetchTweetsNode — using %d pre-loaded tweets (dry-run)", len(existing))
        return {"tweets_raw": existing, "error": ""}

    logger.info("🔍 FetchTweetsNode — querying X API v2 …")

    if not settings.x_bearer_token:
        return {"tweets_raw": [], "error": "X_BEARER_TOKEN not set. Use --dry-run or add to .env."}

    try:
        client = _build_client()
        queries = build_search_queries()

        # Post-game window: last 12 hours (end_time must be ≥30s in the past for X API)
        end_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        start_time = end_time - timedelta(hours=12)

        all_tweets: list[Tweet] = []
        seen_ids: set[str] = set()

        for query in queries:
            logger.info("  Query: %s", query)
            try:
                response = client.search_recent_tweets(
                    query=query,
                    max_results=min(settings.max_tweets_per_query, 100),
                    start_time=start_time,
                    end_time=end_time,
                    tweet_fields=TWEET_FIELDS,
                    user_fields=USER_FIELDS,
                    expansions=EXPANSIONS,
                )
            except tweepy.TooManyRequests:
                logger.warning("  Rate-limited on query, skipping: %s", query)
                continue

            if not response or not response.data:
                logger.info("  No results for query: %s", query)
                continue

            # Build user lookup
            users_map: dict = {}
            if response.includes and "users" in response.includes:
                for u in response.includes["users"]:
                    users_map[u.id] = u

            for tw in response.data:
                tid = str(tw.id)
                if tid not in seen_ids:
                    seen_ids.add(tid)
                    all_tweets.append(_parse_tweet(tw, users_map))

        logger.info("✅ Fetched %d unique tweets", len(all_tweets))

        if len(all_tweets) == 0:
            return {
                "tweets_raw": [],
                "error": "No tweets found in post-game window. Check timing or API access.",
            }

        return {"tweets_raw": all_tweets, "error": ""}

    except Exception as exc:
        logger.exception("FetchTweetsNode failed")
        return {"tweets_raw": [], "error": f"FetchTweetsNode error: {exc}"}
