"""NFL Script Generator — main entry point.

Usage:
    python -m src.main
    python -m src.main --dry-run   (uses mock data instead of live API)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.config import settings
from src.graph import build_graph
from src.models.state import AgentState
from src.models.tweets import Tweet, TweetAuthor, TweetMetrics
from src.utils.logging import setup_logging
from src.utils.output import save_script

logger = logging.getLogger(__name__)


# ── Mock data for dry-run / testing ──────────────────────────

def _mock_tweets() -> list[Tweet]:
    """Return a small set of realistic mock tweets for testing."""
    now = datetime.now(timezone.utc)
    samples = [
        {
            "id": "mock_001",
            "text": "Patrick Mahomes just proved AGAIN why he's the best QB in football. That 4th quarter comeback was insane. Chiefs Kingdom! 🏈🔥",
            "username": "NFLAnalyst",
            "name": "NFL Analyst",
            "followers": 250_000,
            "verified": True,
            "likes": 4500,
            "retweets": 1200,
            "quotes": 350,
            "replies": 800,
            "bio": "NFL analyst for ESPN. 15 years covering football.",
        },
        {
            "id": "mock_002",
            "text": "The refs absolutely ROBBED the Lions today. That pass interference no-call in the end zone changed the entire game. This league has a serious officiating problem.",
            "username": "DetroitBeatWriter",
            "name": "Detroit Beat",
            "followers": 85_000,
            "verified": True,
            "likes": 8200,
            "retweets": 3100,
            "quotes": 900,
            "replies": 2400,
            "bio": "Beat reporter covering the Detroit Lions for The Athletic.",
        },
        {
            "id": "mock_003",
            "text": "Brock Purdy is NOT a system quarterback. Today's performance against the league's #1 defense proves he's elite. 340 yards, 4 TDs, 0 INTs. Put some respect on his name.",
            "username": "PFF",
            "name": "Pro Football Focus",
            "followers": 1_500_000,
            "verified": True,
            "likes": 12000,
            "retweets": 4500,
            "quotes": 1200,
            "replies": 3500,
            "bio": "The leader in football analytics. Data-driven NFL coverage.",
        },
        {
            "id": "mock_004",
            "text": "I've been saying it all year — the Cowboys coaching staff is the problem, not the roster. Another winnable game thrown away by terrible clock management.",
            "username": "CowboysInsider",
            "name": "Cowboys Insider",
            "followers": 120_000,
            "verified": True,
            "likes": 6800,
            "retweets": 2200,
            "quotes": 750,
            "replies": 1900,
            "bio": "Senior NFL correspondent. Former player, 8 years in the league.",
        },
        {
            "id": "mock_005",
            "text": "The Bills defense is SCARY good right now. 6 sacks, 3 turnovers. If they stay healthy, nobody is beating them in January.",
            "username": "NFLDraftScout",
            "name": "NFL Draft Scout",
            "followers": 45_000,
            "verified": False,
            "likes": 2100,
            "retweets": 600,
            "quotes": 180,
            "replies": 420,
            "bio": "Football analyst and draft scout. Film study and player evaluations.",
        },
        {
            "id": "mock_006",
            "text": "Just watched the Eagles lose to a team they should have blown out. Jalen Hurts looks completely lost. Trade deadline can't come soon enough.",
            "username": "PhillyFootball",
            "name": "Philly Football Talk",
            "followers": 68_000,
            "verified": False,
            "likes": 3400,
            "retweets": 980,
            "quotes": 290,
            "replies": 1100,
            "bio": "Philadelphia Eagles coverage. Fan account with hot takes.",
        },
        {
            "id": "mock_007",
            "text": "Lamar Jackson MVP campaign in full force. 3 passing TDs and 95 rushing yards today. He's doing things we've literally never seen a QB do.",
            "username": "RavensReport",
            "name": "Ravens Report",
            "followers": 95_000,
            "verified": True,
            "likes": 7600,
            "retweets": 2800,
            "quotes": 680,
            "replies": 1600,
            "bio": "Covering the Baltimore Ravens. NFL Network contributor.",
        },
        {
            "id": "mock_008",
            "text": "The rookie class this year is DIFFERENT. Five first-round QBs all starting and three of them won today. The NFL is in good hands.",
            "username": "AdamSchefter",
            "name": "Adam Schefter",
            "followers": 10_000_000,
            "verified": True,
            "likes": 25000,
            "retweets": 8500,
            "quotes": 2100,
            "replies": 5200,
            "bio": "ESPN Senior NFL Insider. Breaking news and analysis.",
        },
    ]

    tweets = []
    for s in samples:
        tweets.append(Tweet(
            id=s["id"],
            text=s["text"],
            created_at=now,
            author=TweetAuthor(
                id=f"user_{s['id']}",
                username=s["username"],
                name=s["name"],
                followers_count=s["followers"],
                verified=s["verified"],
                description=s["bio"],
                created_at=datetime(2018, 1, 1, tzinfo=timezone.utc),
            ),
            metrics=TweetMetrics(
                likes=s["likes"],
                retweets=s["retweets"],
                quote_tweets=s["quotes"],
                replies=s["replies"],
            ),
        ))
    return tweets


def run(*, dry_run: bool = False) -> None:
    """Execute the full pipeline."""
    setup_logging(settings.log_level)
    logger.info("🏈 NFL Script Generator — starting pipeline")

    graph = build_graph()

    # Build initial state
    initial_state: dict = {
        "tweets_raw": _mock_tweets() if dry_run else [],
        "tweets_scored": [],
        "tweets_filtered": [],
        "sentiment_clusters": [],
        "dominant_narratives": [],
        "script_outline": None,
        "final_script": None,
        "quality_passed": False,
        "quality_feedback": "",
        "messages": [],
        "error": "",
        "retry_count": 0,
    }

    if dry_run:
        logger.info("🧪 DRY RUN — using mock tweet data (skipping X API)")
        # In dry-run, we skip the fetch node by pre-populating tweets_raw.
        # The graph still starts at fetch, but fetch will see tweets_raw
        # is empty if not dry_run and will call the API. For dry_run we
        # override the fetch node entirely.

    # Run the graph
    final_state = graph.invoke(initial_state)

    # Output
    script = final_state.get("final_script")
    if script:
        out_path = save_script(script, settings.output_dir)
        logger.info("🎉 Pipeline complete! Script saved to %s", out_path)
        print(f"\n{'=' * 72}")
        print(script.render())
        print(f"{'=' * 72}")
    else:
        error = final_state.get("error", "Unknown error")
        logger.error("❌ Pipeline failed: %s", error)
        sys.exit(1)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="NFL YouTube Script Generator")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use mock tweet data instead of live X API",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
