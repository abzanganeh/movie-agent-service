from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Movie:
    title: str
    year: Optional[int]
    genres: List[str]
    imdb_rating: Optional[float]
    metascore: Optional[int]
    certificate: Optional[str]
    director: Optional[str]
    stars: List[str]
    duration_minutes: Optional[int]
    poster_url: Optional[str]
