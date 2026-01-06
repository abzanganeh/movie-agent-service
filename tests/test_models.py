import pytest
from src.movie_agent.models import Movie

def test_movie_creation():
    movie = Movie(
        title="Inception",
        year=2010,
        imdb_rating=8.8,
        genres=["Sci-Fi", "Thriller"],
        director="Christopher Nolan",
        stars=["Leonardo DiCaprio", "Joseph Gordon-Levitt"],
        duration_minutes=148,
        metascore=74,
        certificate="PG-13",
        poster_url="https://example.com/inception.jpg"
    )

    assert movie.title == "Inception"
    assert isinstance(movie.genres, list)
    assert movie.year == 2010
    assert movie.stars[0] == "Leonardo DiCaprio"
