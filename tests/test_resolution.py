"""
Tests for semantic resolution layer.
"""
import pytest
from movie_agent.resolution import (
    SemanticResolver,
    ResolutionResult,
    ExactTitleMatcher,
    FuzzyTitleMatcher,
    ResolutionPolicy,
    MovieTitleResolver,
    VocabularyBuilder,
)
from movie_agent.models import Movie


class TestExactTitleMatcher:
    """Tests for ExactTitleMatcher."""

    def test_exact_match_finds_correct_title(self):
        """Test that exact matcher finds correct title (case-insensitive)."""
        matcher = ExactTitleMatcher()
        candidates = ["Inception", "The Matrix", "Interstellar"]
        
        result = matcher.resolve("Inception", candidates)
        
        assert result.canonical_value == "Inception"
        assert result.confidence == 1.0
        assert result.strategy_used == "exact"
    
    def test_exact_match_case_insensitive(self):
        """Test that exact matcher is case-insensitive."""
        matcher = ExactTitleMatcher()
        candidates = ["Inception", "The Matrix"]
        
        result = matcher.resolve("inception", candidates)
        
        assert result.canonical_value == "Inception"
        assert result.confidence == 1.0
    
    def test_exact_match_no_match(self):
        """Test that exact matcher returns None when no match."""
        matcher = ExactTitleMatcher()
        candidates = ["Inception", "The Matrix"]
        
        result = matcher.resolve("Nonexistent", candidates)
        
        assert result.canonical_value is None
        assert result.confidence == 0.0
        assert result.strategy_used == "exact"


class TestFuzzyTitleMatcher:
    """Tests for FuzzyTitleMatcher."""

    def test_fuzzy_match_corrects_typo(self):
        """Test that fuzzy matcher corrects typos."""
        matcher = FuzzyTitleMatcher(threshold=0.75)
        candidates = ["Inception", "The Matrix", "Interstellar"]
        
        result = matcher.resolve("Inceptoin", candidates)  # Typo
        
        assert result.canonical_value == "Inception"
        assert result.confidence >= 0.75
        assert result.strategy_used == "fuzzy"
    
    def test_fuzzy_match_below_threshold(self):
        """Test that fuzzy matcher rejects matches below threshold."""
        matcher = FuzzyTitleMatcher(threshold=0.9)  # High threshold
        candidates = ["Inception", "The Matrix"]
        
        result = matcher.resolve("CompletelyDifferent", candidates)
        
        assert result.canonical_value is None
        assert result.confidence < 0.9
    
    def test_fuzzy_match_empty_candidates(self):
        """Test that fuzzy matcher handles empty candidates."""
        matcher = FuzzyTitleMatcher()
        
        result = matcher.resolve("Inception", [])
        
        assert result.canonical_value is None
        assert result.confidence == 0.0


class TestResolutionPolicy:
    """Tests for ResolutionPolicy."""

    def test_policy_escalates_exact_to_fuzzy(self):
        """Test that policy tries exact first, then fuzzy."""
        exact = ExactTitleMatcher()
        fuzzy = FuzzyTitleMatcher(threshold=0.75)
        policy = ResolutionPolicy(matchers=[exact, fuzzy], confidence_threshold=0.75)
        candidates = ["Inception", "The Matrix"]
        
        # Exact match should be found first
        result = policy.resolve("Inception", candidates)
        assert result.canonical_value == "Inception"
        assert result.strategy_used == "exact"
        
        # Typo should use fuzzy
        result = policy.resolve("Inceptoin", candidates)
        assert result.canonical_value == "Inception"
        assert result.strategy_used == "fuzzy"
    
    def test_policy_returns_best_result(self):
        """Test that policy returns best result even if below threshold."""
        exact = ExactTitleMatcher()
        fuzzy = FuzzyTitleMatcher(threshold=0.5)  # Low threshold for fuzzy
        policy = ResolutionPolicy(matchers=[exact, fuzzy], confidence_threshold=0.95)  # High policy threshold
        candidates = ["Inception"]
        
        # Fuzzy match exists but below policy threshold
        result = policy.resolve("Inceptoin", candidates)
        
        # Should return best result found (even if below policy threshold)
        # Fuzzy matcher will find match (above its 0.5 threshold)
        # But policy threshold is 0.95, so it should still return the best result
        assert result.canonical_value is not None
        assert result.confidence < 0.95  # Below policy threshold but best available


class TestVocabularyBuilder:
    """Tests for VocabularyBuilder."""

    def test_vocabulary_builds_from_movies(self):
        """Test that vocabulary extracts titles, directors, actors."""
        movies = [
            Movie(
                title="Inception",
                year=2010,
                imdb_rating=8.8,
                genres=["Sci-Fi"],
                director="Christopher Nolan",
                stars=["Leonardo DiCaprio", "Marion Cotillard"],
                duration_minutes=148,
                metascore=74,
                certificate="PG-13",
                poster_url=None,
            ),
            Movie(
                title="The Matrix",
                year=1999,
                imdb_rating=8.7,
                genres=["Action"],
                director="Lana Wachowski",
                stars=["Keanu Reeves"],
                duration_minutes=136,
                metascore=73,
                certificate="R",
                poster_url=None,
            ),
        ]
        
        builder = VocabularyBuilder(movies)
        
        assert "Inception" in builder.get_titles()
        assert "The Matrix" in builder.get_titles()
        assert "Christopher Nolan" in builder.get_directors()
        assert "Leonardo DiCaprio" in builder.get_actors()
        assert "Keanu Reeves" in builder.get_actors()


class TestMovieTitleResolver:
    """Tests for MovieTitleResolver."""

    def test_resolver_corrects_typo(self):
        """Test that resolver corrects typos using fuzzy matching."""
        movies = [
            Movie(
                title="Inception",
                year=2010,
                imdb_rating=None,
                genres=[],
                stars=[],
                director=None,
                duration_minutes=None,
                metascore=None,
                certificate=None,
                poster_url=None,
            ),
            Movie(
                title="The Matrix",
                year=1999,
                imdb_rating=None,
                genres=[],
                stars=[],
                director=None,
                duration_minutes=None,
                metascore=None,
                certificate=None,
                poster_url=None,
            ),
        ]
        vocabulary = VocabularyBuilder(movies)
        resolver = MovieTitleResolver(vocabulary, fuzzy_threshold=0.75)
        
        result = resolver.resolve("Inceptoin")  # Typo
        
        assert result.canonical_value == "Inception"
        assert result.is_confident()
    
    def test_resolver_exact_match_first(self):
        """Test that resolver uses exact match when available."""
        movies = [
            Movie(
                title="Inception",
                year=2010,
                imdb_rating=None,
                genres=[],
                stars=[],
                director=None,
                duration_minutes=None,
                metascore=None,
                certificate=None,
                poster_url=None,
            )
        ]
        vocabulary = VocabularyBuilder(movies)
        resolver = MovieTitleResolver(vocabulary)
        
        result = resolver.resolve("Inception")
        
        assert result.canonical_value == "Inception"
        assert result.strategy_used == "exact"
        assert result.confidence == 1.0

