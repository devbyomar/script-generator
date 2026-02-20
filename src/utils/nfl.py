"""NFL-specific constants and helpers."""

from __future__ import annotations

NFL_TEAMS = [
    "Cardinals", "Falcons", "Ravens", "Bills", "Panthers", "Bears",
    "Bengals", "Browns", "Cowboys", "Broncos", "Lions", "Packers",
    "Texans", "Colts", "Jaguars", "Chiefs", "Raiders", "Chargers",
    "Rams", "Dolphins", "Vikings", "Patriots", "Saints", "Giants",
    "Jets", "Eagles", "Steelers", "49ers", "Seahawks", "Buccaneers",
    "Titans", "Commanders",
]

NFL_SEARCH_TERMS = [
    "NFL", "#NFL", "#NFLSunday", "#SNF", "#MNF", "#TNF",
    "touchdown", "interception", "fumble", "sack",
    "playoffs", "Super Bowl",
]


def build_search_queries(extra_terms: list[str] | None = None) -> list[str]:
    """Build a list of X API search queries for NFL post-game tweets.

    Each query stays under the 512-character limit for the X API v2
    recent search endpoint.
    """
    base_terms = ["NFL", "NFL Sunday", "postgame"]
    if extra_terms:
        base_terms.extend(extra_terms)

    queries: list[str] = []
    for term in base_terms:
        q = f"({term}) lang:en -is:retweet -is:reply"
        queries.append(q)

    return queries
