import os
import pytest
from src.movie_agent.data_loader import MovieDataLoader
from src.movie_agent.models import Movie

CSV_PATH = "data/movies.csv"

@pytest.fixture
def loader():
    return MovieDataLoader(CSV_PATH)

def test_load_movies_returns_list(loader):
    movies = loader.load_movies()
    assert isinstance(movies, list)
    assert all(isinstance(m, Movie) for m in movies)

def test_required_fields_present(loader):
    movies = loader.load_movies()
    for movie in movies:
        assert movie.title is not None
        assert isinstance(movie.genres, list)
        assert isinstance(movie.stars, list)

def test_empty_or_missing_fields(loader):
    movies = loader.load_movies()
    for movie in movies:
        # Year may be None
        assert movie.year is None or isinstance(movie.year, int)
        # IMDb rating may be None
        assert movie.imdb_rating is None or isinstance(movie.imdb_rating, float)
