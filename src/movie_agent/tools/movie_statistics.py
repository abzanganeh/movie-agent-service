"""
Movie statistics tool for dataset-level analytics.

Provides deterministic statistics about the movie dataset.
No LLM dependency - pure data aggregation.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from ..data_loader import MovieDataLoader
from ..models import Movie


class MovieStatisticsInput(BaseModel):
    """Input schema for movie statistics tool."""
    stat_type: Literal["average_rating", "count", "genre_distribution"]
    filter_by: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional filters (e.g., {'year': 2020, 'genre': 'Action'})"
    )


class MovieStatisticsTool(BaseTool):
    """
    Computes statistics about the movie dataset.
    
    Deterministic, no LLM dependency.
    Pure data aggregation for credible demos.
    """
    
    name: str = "get_movie_statistics"
    description: str = (
        "Get statistics about the movie dataset. "
        "Supports: average_rating, count, genre_distribution. "
        "Optional filters by year, genre, etc."
    )
    args_schema: type[BaseModel] = MovieStatisticsInput
    
    def __init__(self, movies: List[Movie] = None, **kwargs):
        """
        Initialize statistics tool with movie dataset.
        
        :param movies: List of Movie objects to analyze
        """
        super().__init__(**kwargs)
        # Use object.__setattr__ to bypass Pydantic v1 validation for private attributes
        if movies is None:
            movies = []
        object.__setattr__(self, '_movies', movies)
    
    def _run(
        self,
        stat_type: str,
        filter_by: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Compute statistics on the movie dataset.
        
        :param stat_type: Type of statistic to compute
        :param filter_by: Optional filters to apply
        :return: JSON string with statistics
        """
        # Check if movies are available (use getattr to safely access private attribute)
        # This works with both Pydantic v1 and v2
        movies = getattr(self, '_movies', [])
        if not movies:
            return '{"error": "Movie dataset not loaded. Statistics tool unavailable."}'
        
        # Apply filters if provided
        filtered_movies = self._apply_filters(movies, filter_by)
        
        if not filtered_movies:
            return '{"error": "No movies match the filters"}'
        
        if stat_type == "average_rating":
            ratings = [
                m.imdb_rating for m in filtered_movies
                if m.imdb_rating is not None
            ]
            if not ratings:
                return '{"average_rating": null, "note": "No ratings available"}'
            avg = sum(ratings) / len(ratings)
            return f'{{"average_rating": {avg:.2f}, "count": {len(ratings)}}}'
        
        if stat_type == "count":
            return f'{{"count": {len(filtered_movies)}}}'
        
        if stat_type == "genre_distribution":
            dist = {}
            for movie in filtered_movies:
                for genre in movie.genres:
                    dist[genre] = dist.get(genre, 0) + 1
            return f'{{"genre_distribution": {dist}}}'
        
        return '{"error": "Unknown stat_type"}'
    
    def _apply_filters(
        self,
        movies: List[Movie],
        filter_by: Optional[Dict[str, Any]]
    ) -> List[Movie]:
        """Apply filters to movie list."""
        if not filter_by:
            return movies
        
        filtered = movies
        
        # Filter by year
        if "year" in filter_by:
            year = filter_by["year"]
            filtered = [m for m in filtered if m.year == year]
        
        # Filter by genre
        if "genre" in filter_by:
            genre = filter_by["genre"].lower()
            filtered = [
                m for m in filtered
                if any(g.lower() == genre for g in m.genres)
            ]
        
        # Filter by director
        if "director" in filter_by:
            director = filter_by["director"].lower()
            filtered = [
                m for m in filtered
                if m.director and m.director.lower() == director
            ]
        
        return filtered
    
    async def _arun(
        self,
        stat_type: str,
        filter_by: Optional[Dict[str, Any]] = None
    ) -> str:
        """Async version of _run."""
        return self._run(stat_type, filter_by)

