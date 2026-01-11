from typing import List
from .models import Movie
from langchain_core.documents import Document

class MovieCanonicalizer:
    @staticmethod
    def to_text(movie: Movie) -> str:
        parts = [f"Title: {movie.title}"]

        if movie.year:
            parts.append(f"Year: {movie.year}")

        if movie.genres:
            parts.append(f"Genres: {', '.join(movie.genres)}")

        if movie.director:
            parts.append(f"Director: {movie.director}")

        if movie.stars:
            parts.append(f"Stars: {', '.join(movie.stars)}")

        if movie.imdb_rating:
            parts.append(f"IMDb Rating: {movie.imdb_rating}")

        if movie.metascore:
            parts.append(f"Metascore: {movie.metascore}")

        if movie.duration_minutes:
            parts.append(f"Duration: {movie.duration_minutes} minutes")

        return ". ".join(parts) + "."

def build_documents(movies: List[Movie]) -> List[Document]:
    """
    Build Document objects from Movie objects with complete metadata.
    
    OOP: Single Responsibility - converts Movie domain objects to Document objects.
    Includes all metadata fields needed for quiz generation (director, stars, etc.)
    """
    documents: List[Document] = []

    for movie in movies:
        text = MovieCanonicalizer.to_text(movie)
        # OOP: Encapsulation - include all relevant metadata for quiz generation
        metadata = {
            "title": movie.title,
            "year": movie.year,
            "rating": movie.imdb_rating,
            "director": movie.director,  # Required for director quiz
            "stars": movie.stars,  # Required for cast quiz (from CSV "Star Cast" column)
            "genres": movie.genres,
            "duration_minutes": movie.duration_minutes,
            "metascore": movie.metascore,
            "certificate": movie.certificate,
            "poster_url": movie.poster_url,
        }
        documents.append(Document(page_content=text, metadata=metadata))

    return documents
