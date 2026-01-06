from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Movie:
    title: str
    year: Optional[int]
    imdb_rating: Optional[float]
    genres: List[str]
    director: Optional[str]
    stars: List[str]
    duration_minutes: Optional[int]
    metascore: Optional[int]
    certificate: Optional[str]
    poster_url: Optional[str]

  