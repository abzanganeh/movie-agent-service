"""
Tests for movie statistics tool.
"""
import pytest
from movie_agent.tools.movie_statistics import MovieStatisticsTool, MovieStatisticsInput
from movie_agent.models import Movie


class TestMovieStatisticsTool:
    """Tests for MovieStatisticsTool."""

    def test_average_rating(self):
        """Test average rating calculation."""
        movies = [
            Movie(
                title="Movie 1", year=2020, imdb_rating=8.0,
                genres=[], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
            Movie(
                title="Movie 2", year=2021, imdb_rating=7.0,
                genres=[], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
            Movie(
                title="Movie 3", year=2022, imdb_rating=9.0,
                genres=[], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
        ]
        
        tool = MovieStatisticsTool(movies=movies)
        result = tool._run("average_rating")
        
        assert "average_rating" in result
        assert "8.00" in result  # (8.0 + 7.0 + 9.0) / 3 = 8.0

    def test_count(self):
        """Test count calculation."""
        movies = [
            Movie(
                title="Movie 1", year=2020, imdb_rating=None,
                genres=[], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
            Movie(
                title="Movie 2", year=2021, imdb_rating=None,
                genres=[], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
        ]
        
        tool = MovieStatisticsTool(movies=movies)
        result = tool._run("count")
        
        assert '"count": 2' in result

    def test_genre_distribution(self):
        """Test genre distribution calculation."""
        movies = [
            Movie(
                title="Movie 1", year=2020, imdb_rating=None,
                genres=["Action", "Sci-Fi"], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
            Movie(
                title="Movie 2", year=2021, imdb_rating=None,
                genres=["Action", "Drama"], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
        ]
        
        tool = MovieStatisticsTool(movies=movies)
        result = tool._run("genre_distribution")
        
        assert "Action" in result
        assert "Sci-Fi" in result
        assert "Drama" in result

    def test_filter_by_year(self):
        """Test filtering by year."""
        movies = [
            Movie(
                title="Movie 1", year=2020, imdb_rating=8.0,
                genres=[], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
            Movie(
                title="Movie 2", year=2021, imdb_rating=7.0,
                genres=[], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
        ]
        
        tool = MovieStatisticsTool(movies=movies)
        result = tool._run("count", filter_by={"year": 2020})
        
        assert '"count": 1' in result

    def test_filter_by_genre(self):
        """Test filtering by genre."""
        movies = [
            Movie(
                title="Movie 1", year=2020, imdb_rating=None,
                genres=["Action"], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
            Movie(
                title="Movie 2", year=2021, imdb_rating=None,
                genres=["Drama"], stars=[], director=None,
                duration_minutes=None, metascore=None, certificate=None, poster_url=None
            ),
        ]
        
        tool = MovieStatisticsTool(movies=movies)
        result = tool._run("count", filter_by={"genre": "Action"})
        
        assert '"count": 1' in result

