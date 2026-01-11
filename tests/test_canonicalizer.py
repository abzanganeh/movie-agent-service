import pytest
from src.movie_agent.models import Movie
from src.movie_agent.canonicalizer import MovieCanonicalizer

def test_canonical_text_basic():
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

    text = MovieCanonicalizer.to_text(movie)
    assert "Title: Inception" in text
    assert "Year: 2010" in text
    assert "Genres: Sci-Fi, Thriller" in text
    assert "Stars: Leonardo DiCaprio, Joseph Gordon-Levitt" in text
    # Ensure deterministic ordering
    assert text.startswith("Title: Inception. Year: 2010")
