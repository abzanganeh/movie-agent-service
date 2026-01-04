"""
Tests for intent router.
"""
import pytest
from movie_agent.interaction import IntentRouter, IntentType


class TestIntentRouter:
    """Tests for IntentRouter."""

    def test_greeting_intent(self):
        """Test greeting detection."""
        router = IntentRouter()
        
        assert router.route("hi") == IntentType.GREETING
        assert router.route("hello") == IntentType.GREETING
        assert router.route("hey") == IntentType.GREETING

    def test_game_intent(self):
        """Test game/quiz intent detection."""
        router = IntentRouter()
        
        assert router.route("play game") == IntentType.GAME
        assert router.route("movie quiz") == IntentType.GAME
        assert router.route("quiz") == IntentType.GAME
        assert router.route("trivia") == IntentType.GAME

    def test_compare_intent(self):
        """Test compare intent detection."""
        router = IntentRouter()
        
        assert router.route("compare Inception vs Matrix") == IntentType.COMPARE_MOVIES
        assert router.route("Inception versus Matrix") == IntentType.COMPARE_MOVIES
        assert router.route("better than") == IntentType.COMPARE_MOVIES

    def test_statistics_intent(self):
        """Test statistics intent detection."""
        router = IntentRouter()
        
        assert router.route("stats movies by year") == IntentType.STATISTICS
        assert router.route("statistics") == IntentType.STATISTICS
        assert router.route("average rating") == IntentType.STATISTICS

    def test_poster_analysis_intent(self):
        """Test poster analysis intent detection."""
        router = IntentRouter()
        
        assert router.route("analyze poster at path/to/image.png") == IntentType.POSTER_ANALYSIS
        assert router.route("poster analysis") == IntentType.POSTER_ANALYSIS
        assert router.route("image.jpg") == IntentType.POSTER_ANALYSIS

    def test_movie_search_intent(self):
        """Test movie search intent detection."""
        router = IntentRouter()
        
        assert router.route("find sci-fi movies") == IntentType.MOVIE_SEARCH
        assert router.route("recommend movies") == IntentType.MOVIE_SEARCH
        assert router.route("search for action films") == IntentType.MOVIE_SEARCH

    def test_unknown_intent(self):
        """Test unknown intent for meaningless queries."""
        router = IntentRouter()
        
        # Short meaningless queries
        assert router.route("play") == IntentType.UNKNOWN
        assert router.route("fun") == IntentType.UNKNOWN
        assert router.route("let have fun") == IntentType.UNKNOWN
        
        # Empty query
        assert router.route("") == IntentType.UNKNOWN
        assert router.route("   ") == IntentType.UNKNOWN

    def test_case_insensitive(self):
        """Test that routing is case-insensitive."""
        router = IntentRouter()
        
        assert router.route("HI") == IntentType.GREETING
        assert router.route("Play Game") == IntentType.GAME
        assert router.route("COMPARE MOVIES") == IntentType.COMPARE_MOVIES

