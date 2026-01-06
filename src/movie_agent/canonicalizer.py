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
    documents: List[Document] = []

    for movie in movies:
        text = MovieCanonicalizer.to_text(movie)
        metadata = {
            "title": movie.title,
            "year": movie.year,
            "rating": movie.imdb_rating,
        }
        documents.append(Document(page_content=text, metadata=metadata))

    return documents
