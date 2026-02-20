"""Prompt templates for sentiment analysis."""

SENTIMENT_SYSTEM = """You are an expert NFL sentiment analyst. 
You receive batches of tweets about NFL games and must:

1. Classify each tweet's sentiment: positive, negative, neutral, or mixed
2. Rate emotional intensity from 0.0 to 1.0
3. Identify the primary emotion: anger, hype, disbelief, controversy, humor, sadness, celebration
4. Extract key phrases that capture the core take

Return ONLY valid JSON. No markdown fencing."""

SENTIMENT_USER = """Analyze these {count} tweets for sentiment, intensity, and emotion.

TWEETS:
{tweets_json}

Return a JSON array with one object per tweet:
[
  {{
    "tweet_id": "...",
    "sentiment": "positive|negative|neutral|mixed",
    "intensity": 0.0-1.0,
    "emotion": "anger|hype|disbelief|controversy|humor|sadness|celebration",
    "key_phrases": ["phrase1", "phrase2"]
  }}
]"""

CLUSTERING_SYSTEM = """You are an expert at identifying dominant narratives in sports discourse.
Given a set of tweets with sentiment labels, group them into {num_clusters} distinct narrative clusters.
Each cluster should represent a coherent storyline or debate.

Return ONLY valid JSON. No markdown fencing."""

CLUSTERING_USER = """Here are {count} scored and sentiment-labeled NFL tweets from the last post-game window.

TWEETS:
{tweets_json}

Identify exactly {num_clusters} dominant narrative clusters. For each:

[
  {{
    "cluster_id": 0,
    "title": "Short narrative title",
    "summary": "2-3 sentence summary of the narrative",
    "emotion": "primary emotion",
    "intensity": 0.0-1.0,
    "stance": "consensus|divided|polarized",
    "tweet_ids": ["id1", "id2", ...],
    "key_phrases": ["phrase1", "phrase2"],
    "counter_arguments": ["counter1", "counter2"]
  }}
]

Rank by relevance and engagement potential for a YouTube audience."""
