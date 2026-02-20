"""Narrative and sentiment cluster models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SentimentCluster(BaseModel):
    """Group of tweets sharing a sentiment + topic."""

    cluster_id: int
    label: str = ""                        # e.g. "anger at officiating"
    sentiment: str = ""                    # positive / negative / neutral / mixed
    intensity: float = 0.0                 # 0‑1
    tweet_ids: list[str] = Field(default_factory=list)
    representative_texts: list[str] = Field(default_factory=list)
    size: int = 0


class Narrative(BaseModel):
    """A dominant narrative extracted from clustered sentiment."""

    title: str                             # e.g. "Refs Cost the Chiefs the Game"
    summary: str                           # 2-3 sentence summary
    emotion: str                           # primary emotion driving this narrative
    intensity: float = 0.0                 # 0‑1
    stance: str = "divided"                # consensus / divided / polarized
    supporting_tweet_ids: list[str] = Field(default_factory=list)
    key_phrases: list[str] = Field(default_factory=list)
    counter_arguments: list[str] = Field(default_factory=list)
    relevance_score: float = 0.0           # 0‑100
