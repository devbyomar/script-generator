"""Tests for data models."""

from __future__ import annotations

from datetime import datetime, timezone

from src.models.tweets import Tweet, TweetAuthor, TweetMetrics
from src.models.narratives import Narrative, SentimentCluster
from src.models.script import FinalScript, ScriptSection, ScriptOutline, QualityReport


class TestTweetAuthor:
    def test_account_age_days(self):
        author = TweetAuthor(
            id="1",
            username="test",
            name="Test",
            created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        assert author.account_age_days > 0

    def test_engagement_ratio(self):
        author = TweetAuthor(
            id="1",
            username="test",
            name="Test",
            followers_count=1000,
            tweet_count=100,
        )
        assert author.engagement_ratio == 0.1


class TestTweet:
    def test_defaults(self):
        tw = Tweet(
            id="1",
            text="hello",
            created_at=datetime.now(timezone.utc),
            author=TweetAuthor(id="a", username="u", name="n"),
            metrics=TweetMetrics(),
        )
        assert tw.engagement_score == 0.0
        assert tw.credibility_score == 0.0
        assert tw.sentiment_label == ""
        assert tw.narrative_cluster == -1


class TestNarrative:
    def test_creation(self):
        n = Narrative(
            title="Test Narrative",
            summary="A test",
            emotion="hype",
        )
        assert n.stance == "divided"
        assert n.relevance_score == 0.0


class TestFinalScript:
    def test_render(self):
        script = FinalScript(
            title="Test Video",
            thumbnail_text="WOW",
            description="A test video",
            sections=[
                ScriptSection(
                    section_name="Hook",
                    timestamp="0:00-0:20",
                    content="What if I told you...",
                    stage_direction="Fast-paced, intense",
                )
            ],
        )
        rendered = script.render()
        assert "Test Video" in rendered
        assert "What if I told you" in rendered
        assert "Hook" in rendered
