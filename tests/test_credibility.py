"""Tests for credibility scoring logic."""

from __future__ import annotations

from datetime import datetime, timezone

from src.models.tweets import Tweet, TweetAuthor, TweetMetrics
from src.scoring.credibility import compute_credibility, score_credibility


def _make_tweet(
    username: str = "tester",
    followers: int = 10_000,
    verified: bool = False,
    bio: str = "",
    account_age_days: int = 1000,
) -> Tweet:
    created = datetime.now(timezone.utc)
    from datetime import timedelta
    acct_created = created - timedelta(days=account_age_days)
    return Tweet(
        id="test_cred_1",
        text="Test tweet",
        created_at=created,
        author=TweetAuthor(
            id="author_cred_1",
            username=username,
            name="Test User",
            followers_count=followers,
            verified=verified,
            description=bio,
            created_at=acct_created,
        ),
        metrics=TweetMetrics(likes=100, retweets=50, quote_tweets=10, replies=30),
    )


class TestCredibility:
    def test_verified_gets_boost(self):
        unverified = _make_tweet(verified=False)
        verified = _make_tweet(verified=True)
        assert compute_credibility(verified) > compute_credibility(unverified)

    def test_high_followers_scores_higher(self):
        small = _make_tweet(followers=1_000)
        big = _make_tweet(followers=500_000)
        assert compute_credibility(big) > compute_credibility(small)

    def test_insider_bio_scores_higher(self):
        generic = _make_tweet(bio="I love football")
        insider = _make_tweet(bio="NFL insider and senior analyst for ESPN")
        assert compute_credibility(insider) > compute_credibility(generic)

    def test_parody_account_penalised(self):
        real = _make_tweet(bio="NFL analyst", verified=True, followers=100_000)
        parody = _make_tweet(bio="Parody account, not affiliated with the NFL", verified=False, followers=100_000)
        assert compute_credibility(real) > compute_credibility(parody)

    def test_known_handle_scores_higher(self):
        unknown = _make_tweet(username="randomfan123")
        known = _make_tweet(username="adamschefter")
        assert compute_credibility(known) > compute_credibility(unknown)


class TestScoreCredibility:
    def test_filters_by_min_score(self):
        tw_low = _make_tweet(followers=500, bio="casual fan")
        tw_low.id = "low"
        tw_high = _make_tweet(followers=500_000, verified=True, bio="NFL insider for ESPN")
        tw_high.id = "high"
        result = score_credibility([tw_low, tw_high], min_score=30.0)
        assert all(t.credibility_score >= 30.0 for t in result)
