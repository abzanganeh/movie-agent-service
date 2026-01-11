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
        """
        Parse a list from CSV value.
        
        Handles multiple formats:
        - Comma-separated: "Name1, Name2, Name3"
        - Pipe-separated: "Name1|Name2|Name3"
        - Concatenated (no separators): "Name1Name2Name3" (splits on capital letters after lowercase)
        """
        if not value:
            return []
        
        # First try standard separators (comma or pipe)
        if "," in value or "|" in value:
            return [v.strip() for v in re.split(r",|\|", value) if v.strip()]
        
        # Handle concatenated names (e.g., "John SmithJane Doe" -> ["John Smith", "Jane Doe"])
        # Pattern: Split on capital letter that follows lowercase letter or digit
        # This handles: "Cliff HollingsworthAkiva Goldsman" -> ["Cliff Hollingsworth", "Akiva Goldsman"]
        parts = re.split(r'(?<=[a-z0-9])(?=[A-Z])', value)
        # Filter out empty strings and strip whitespace
        result = [v.strip() for v in parts if v.strip()]
        
        # If splitting didn't work (e.g., all caps or single name), return as single item
        if not result:
            return [value.strip()] if value.strip() else []
        
        return result
