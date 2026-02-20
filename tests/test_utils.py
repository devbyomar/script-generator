"""Tests for utility functions."""

from __future__ import annotations

from src.utils.nfl import NFL_TEAMS, build_search_queries


class TestNFLUtils:
    def test_team_count(self):
        assert len(NFL_TEAMS) == 32

    def test_build_queries_default(self):
        queries = build_search_queries()
        assert len(queries) >= 3
        assert all("lang:en" in q for q in queries)
        assert all("-is:retweet" in q for q in queries)

    def test_build_queries_with_extras(self):
        queries = build_search_queries(extra_terms=["Mahomes", "Chiefs"])
        assert len(queries) >= 5  # base 3 + 2 extras
