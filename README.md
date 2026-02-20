# 🏈 NFL YouTube Script Generator

A production-ready **LangGraph** agent that autonomously generates high-engagement, full-length YouTube scripts (8–12 min) for an NFL-focused channel by aggregating public post-game sentiment from X (Twitter).

## Architecture

```
Fetch → Score → Filter → Cluster → Extract → Outline → Generate → Validate
                                                                      ↓
                                                             (retry if failed)
```

| Node | Purpose |
|---|---|
| `FetchTweetsNode` | Pull NFL tweets from X API v2 (post-game window) |
| `EngagementScoringNode` | Weighted score: Likes×1 + RT×2 + QT×3 + Replies×2.5 |
| `CredibilityFilterNode` | Score by verification, bio, follower count, outlet |
| `SentimentClusteringNode` | LLM-powered sentiment + intensity analysis |
| `NarrativeExtractionNode` | Identify 3–5 dominant narratives |
| `ScriptOutlineNode` | Produce structured outline (9 retention sections) |
| `ScriptGenerationNode` | Write the full spoken-word script |
| `QualityCheckNode` | Evaluate retention, authenticity, pacing (auto-retry) |

## Quick Start

```bash
# 1. Clone & enter
git clone https://github.com/devbyomar/script-generator.git
cd script-generator

# 2. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your X_BEARER_TOKEN and OPENAI_API_KEY

# 5. Run with mock data (no API keys needed)
python -m src.main --dry-run

# 6. Run with live X API data
python -m src.main
```

## Project Structure

```
src/
├── __init__.py
├── __main__.py          # python -m src entry
├── main.py              # CLI + dry-run logic
├── config.py            # Pydantic settings from .env
├── graph.py             # LangGraph pipeline definition
├── models/
│   ├── state.py         # AgentState TypedDict
│   ├── tweets.py        # Tweet, TweetAuthor, TweetMetrics
│   ├── narratives.py    # Narrative, SentimentCluster
│   └── script.py        # ScriptOutline, FinalScript, QualityReport
├── nodes/
│   ├── fetch_tweets.py
│   ├── engagement_scoring.py
│   ├── credibility_filter.py
│   ├── sentiment_clustering.py
│   ├── narrative_extraction.py
│   ├── script_outline.py
│   ├── script_generation.py
│   └── quality_check.py
├── prompts/
│   ├── sentiment.py     # Sentiment + clustering prompts
│   └── script.py        # Outline, script, quality prompts
├── scoring/
│   ├── engagement.py    # Weighted engagement scoring
│   └── credibility.py   # Author credibility scoring
└── utils/
    ├── logging.py       # Rich logging setup
    ├── nfl.py           # Team lists, search query builder
    └── output.py        # Save scripts to output/
```

## Script Structure (Retention Framework)

1. **Pattern Interrupt Hook** (0:00–0:20)
2. **Emotional Framing** (0:20–1:00)
3. **Narrative Build-Up** (1:00–3:00)
4. **Evidence & Public Sentiment** (3:00–5:00)
5. **Counterargument** (5:00–6:00)
6. **Escalation** (6:00–8:00)
7. **Big Take** (8:00–9:30)
8. **Closing Loop Callback** (9:30–10:00)
9. **CTA** (10:00–10:30)

## Testing

```bash
pytest tests/ -v
```

## Compliance

- Uses **official X API v2** only (no scraping)
- Respects rate limits via `wait_on_rate_limit=True`
- Tweets are paraphrased, never read verbatim
- Includes disclaimers where necessary

## Scaling Notes

- Add Redis/Postgres for tweet caching across runs
- Parallel query execution for multiple game windows
- A/B test thumbnails via YouTube API integration
- Schedule via cron / Cloud Functions for automated Sunday runs
- Add affiliate/merch tie-in sections via prompt template extension