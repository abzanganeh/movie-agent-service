import csv
from typing import List, Optional
import re
from .models import Movie


class MovieDataLoader:
    """
    Loads and normalizes movie data from CSV.
    """
    def __init__(self, csv_path: str):
        self.csv_path = csv_path

    def load_movies(self) -> List[Movie]:
        movies: List[Movie] = []

        with open(self.csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                movie = self._parse_row(row)
                if movie:
                    movies.append(movie)

        return movies

    def _parse_row(self, row: dict) -> Optional[Movie]:
        title = self._clean_text(row.get("Title"))
        if not title:
            return None

        return Movie(
            title=title,
            year=self._parse_int(row.get("Year")),
            imdb_rating=self._parse_float(row.get("IMDb Rating")),
            genres=self._parse_list(row.get("Genre")),
            director=self._clean_text(row.get("Director")),
            stars=self._parse_list(row.get("Star Cast")),
            duration_minutes=self._parse_int(row.get("Duration (minutes)")),
            metascore=self._parse_int(row.get("MetaScore")),
            certificate=self._clean_text(row.get("Certificates")),
            poster_url=self._clean_text(row.get("Poster-src")),
        )

    def _clean_text(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value if value else None

    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        try:
            return int(re.findall(r"\d+", value)[0])
        except Exception:
            return None

    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        try:
            return float(value)
        except Exception:
            return None

    def _parse_list(self, value: Optional[str]) -> List[str]:
        if not value:
            return []
        return [v.strip() for v in re.split(r",|\|", value) if v.strip()]
