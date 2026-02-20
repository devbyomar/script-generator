"""Tweet data models."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class TweetAuthor(BaseModel):
    """Public metadata about a tweet author."""

    id: str
    username: str
    name: str
    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    verified: bool = False
    description: str = ""
    created_at: datetime | None = None

    @property
    def account_age_days(self) -> int:
        if self.created_at is None:
            return 0
        now = datetime.now(timezone.utc)
        # Handle naive datetimes by assuming UTC
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return max((now - created).days, 1)

    @property
    def engagement_ratio(self) -> float:
        """Ratio of tweet activity to followers — proxy for real engagement."""
        if self.followers_count == 0:
            return 0.0
        return self.tweet_count / self.followers_count


class TweetMetrics(BaseModel):
    """Public engagement metrics."""

    likes: int = 0
    retweets: int = 0
    quote_tweets: int = 0
    replies: int = 0


class Tweet(BaseModel):
    """Normalised tweet record used throughout the pipeline."""

    id: str
    text: str
    created_at: datetime
    author: TweetAuthor
    metrics: TweetMetrics
    conversation_id: str | None = None
    referenced_tweet_ids: list[str] = Field(default_factory=list)
    context_annotations: list[str] = Field(default_factory=list)

    # ── Computed downstream ──────────────────────────────
    engagement_score: float = 0.0
    credibility_score: float = 0.0
    sentiment_label: str = ""           # positive / negative / neutral / mixed
    sentiment_intensity: float = 0.0    # 0‑1
    narrative_cluster: int = -1
