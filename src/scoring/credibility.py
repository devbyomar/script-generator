"""Credibility scoring for tweet authors.

Higher score → more authoritative source.
"""

from __future__ import annotations

import logging
import re

from src.models.tweets import Tweet

logger = logging.getLogger(__name__)

# ── Known high-authority patterns ────────────────────────────
INSIDER_KEYWORDS = [
    "nfl insider", "nfl network", "espn", "beat reporter", "reporter",
    "analyst", "correspondent", "nfl draft", "senior writer",
    "staff writer", "columnist", "editor", "host",
]

FORMER_PLAYER_KEYWORDS = [
    "former nfl", "retired nfl", "super bowl champion", "pro bowl",
    "ex-nfl", "played in the nfl", "nfl veteran",
]

MAJOR_OUTLETS = [
    "espn", "nfl", "theringer", "theathletic", "bleacherreport",
    "foxsports", "cbssports", "nbcsports", "profootballtalk",
    "pff", "nflnetwork", "adamschefter", "rapsheet",
    "fieldyates", "diannaespn", "taborgate",
]


def _bio_match(bio: str, keywords: list[str]) -> float:
    """Return a score boost (0-30) based on bio keyword matches."""
    bio_lower = bio.lower()
    hits = sum(1 for kw in keywords if kw in bio_lower)
    return min(hits * 10.0, 30.0)


def _handle_match(username: str) -> float:
    """Return a score boost (0-25) if username is a known outlet / insider."""
    handle = username.lower()
    hits = sum(1 for outlet in MAJOR_OUTLETS if outlet in handle)
    return min(hits * 25.0, 25.0)


def compute_credibility(tweet: Tweet) -> float:
    """Return a 0–100 credibility score for a tweet author."""
    score = 0.0
    author = tweet.author

    # Verification status
    if author.verified:
        score += 20.0

    # Follower count tiers
    if author.followers_count >= 500_000:
        score += 25.0
    elif author.followers_count >= 100_000:
        score += 20.0
    elif author.followers_count >= 25_000:
        score += 12.0
    elif author.followers_count >= 5_000:
        score += 6.0

    # Bio analysis
    score += _bio_match(author.description, INSIDER_KEYWORDS)
    score += _bio_match(author.description, FORMER_PLAYER_KEYWORDS) * 0.8

    # Handle matching
    score += _handle_match(author.username)

    # Account age (older = more trustworthy, max 10 pts)
    if author.account_age_days >= 365 * 5:
        score += 10.0
    elif author.account_age_days >= 365 * 2:
        score += 6.0
    elif author.account_age_days >= 365:
        score += 3.0

    # Penalise likely meme / fan accounts
    meme_patterns = re.compile(
        r"(parody|meme|fan page|not affiliated|satire)", re.IGNORECASE
    )
    if meme_patterns.search(author.description):
        score *= 0.3

    return round(min(score, 100.0), 2)


def score_credibility(tweets: list[Tweet], min_score: float = 0.0) -> list[Tweet]:
    """Assign credibility scores and optionally filter by minimum."""
    result: list[Tweet] = []
    for tw in tweets:
        tw.credibility_score = compute_credibility(tw)
        if tw.credibility_score >= min_score:
            result.append(tw)

    result.sort(key=lambda t: t.credibility_score, reverse=True)
    logger.info(
        "Credibility filtering: %d kept (from %d), min=%.1f",
        len(result), len(tweets), min_score,
    )
    return result
