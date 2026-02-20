"""Tests for engagement scoring logic."""

from __future__ import annotations

from datetime import datetime, timezone

from src.models.tweets import Tweet, TweetAuthor, TweetMetrics
from src.scoring.engagement import (
    compute_raw_engagement,
    normalise_engagement,
    passes_filter,
    score_tweets,
)


def _make_tweet(
    likes: int = 100,
    retweets: int = 50,
    quotes: int = 10,
    replies: int = 30,
    followers: int = 10_000,
    verified: bool = False,
    tweet_count: int = 5000,
    account_age_days: int = 1000,
) -> Tweet:
    created = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return Tweet(
        id="test_1",
        text="Test tweet",
        created_at=datetime.now(timezone.utc),
        author=TweetAuthor(
            id="author_1",
            username="tester",
            name="Tester",
            followers_count=followers,
            tweet_count=tweet_count,
            verified=verified,
            description="NFL analyst",
            created_at=created,
        ),
        metrics=TweetMetrics(
            likes=likes,
            retweets=retweets,
            quote_tweets=quotes,
            replies=replies,
        ),
    )


class TestRawEngagement:
    def test_weighted_formula(self):
        tw = _make_tweet(likes=100, retweets=50, quotes=10, replies=30)
        raw = compute_raw_engagement(tw)
        expected = 100 * 1.0 + 50 * 2.0 + 10 * 3.0 + 30 * 2.5
        assert raw == expected

    def test_zero_engagement(self):
        tw = _make_tweet(likes=0, retweets=0, quotes=0, replies=0)
        assert compute_raw_engagement(tw) == 0.0


class TestNormalisation:
    def test_verified_boost(self):
        tw_unverified = _make_tweet(verified=False)
        tw_verified = _make_tweet(verified=True)
        raw = compute_raw_engagement(tw_unverified)
        score_unverified = normalise_engagement(raw, tw_unverified)
        score_verified = normalise_engagement(raw, tw_verified)
        assert score_verified > score_unverified

    def test_higher_followers_lower_normalised(self):
        tw_small = _make_tweet(followers=1_000)
        tw_big = _make_tweet(followers=1_000_000)
        raw = compute_raw_engagement(tw_small)
        assert normalise_engagement(raw, tw_small) > normalise_engagement(raw, tw_big)


class TestFilter:
    def test_small_account_low_engagement_rejected(self):
        # 500 followers, 10 tweets → ratio = 10/500 = 2% (below 5% threshold)
        tw = _make_tweet(followers=500, tweet_count=10)
        assert not passes_filter(tw)

    def test_small_account_high_engagement_kept(self):
        tw = _make_tweet(followers=500, tweet_count=100)
        tw.author.tweet_count = 50  # ratio = 50/500 = 10%
        assert passes_filter(tw)

    def test_zero_metrics_rejected(self):
        tw = _make_tweet(likes=0, retweets=0, quotes=0, replies=0)
        assert not passes_filter(tw)


class TestScoreTweets:
    def test_returns_sorted_descending(self):
        tw1 = _make_tweet(likes=10, retweets=5, quotes=1, replies=3)
        tw2 = _make_tweet(likes=1000, retweets=500, quotes=100, replies=300)
        tw2.id = "test_2"
        result = score_tweets([tw1, tw2])
        assert len(result) >= 1
        if len(result) == 2:
            assert result[0].engagement_score >= result[1].engagement_score
