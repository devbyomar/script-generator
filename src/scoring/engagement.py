"""Engagement scoring logic.

WeightedScore = (Likes × 1) + (Retweets × 2) + (QuoteTweets × 3) + (Replies × 2.5)
Normalised by follower count, account age, and verification status.
"""

from __future__ import annotations

import logging
import math

from src.models.tweets import Tweet

logger = logging.getLogger(__name__)

# ── Weight constants ──────────────────────────────────────────
LIKE_WEIGHT = 1.0
RETWEET_WEIGHT = 2.0
QUOTE_WEIGHT = 3.0
REPLY_WEIGHT = 2.5

# ── Normalisation factors ────────────────────────────────────
VERIFIED_BOOST = 1.5
MIN_FOLLOWERS_HARD = 1_000
MIN_ENGAGEMENT_RATIO = 0.05  # 5%


def compute_raw_engagement(tweet: Tweet) -> float:
    """Return the un-normalised weighted engagement score."""
    m = tweet.metrics
    return (
        m.likes * LIKE_WEIGHT
        + m.retweets * RETWEET_WEIGHT
        + m.quote_tweets * QUOTE_WEIGHT
        + m.replies * REPLY_WEIGHT
    )


def normalise_engagement(raw: float, tweet: Tweet) -> float:
    """Normalise raw score using follower count, account age, and verification."""
    followers = max(tweet.author.followers_count, 1)
    age_days = max(tweet.author.account_age_days, 1)

    # Log-scale follower normalisation to avoid crushing smaller accounts
    follower_factor = math.log10(followers + 1)

    # Age factor — older accounts get a slight boost (capped)
    age_factor = min(math.log10(age_days + 1), 3.0) / 3.0  # 0-1 range

    normalised = raw / follower_factor * (0.7 + 0.3 * age_factor)

    if tweet.author.verified:
        normalised *= VERIFIED_BOOST

    return round(normalised, 4)


def passes_filter(tweet: Tweet) -> bool:
    """Return True if the tweet should NOT be filtered out as spam/bot."""
    author = tweet.author

    # Allow small accounts only if engagement ratio is very high
    if author.followers_count < MIN_FOLLOWERS_HARD:
        if author.engagement_ratio < MIN_ENGAGEMENT_RATIO:
            return False

    # Reject if zero engagement at all
    m = tweet.metrics
    if m.likes + m.retweets + m.quote_tweets + m.replies == 0:
        return False

    return True


def score_tweets(tweets: list[Tweet]) -> list[Tweet]:
    """Score and filter a batch of tweets. Returns scored list (may be smaller)."""
    scored: list[Tweet] = []
    for tw in tweets:
        if not passes_filter(tw):
            continue
        raw = compute_raw_engagement(tw)
        tw.engagement_score = normalise_engagement(raw, tw)
        scored.append(tw)

    scored.sort(key=lambda t: t.engagement_score, reverse=True)
    logger.info("Scored %d tweets (from %d raw)", len(scored), len(tweets))
    return scored
