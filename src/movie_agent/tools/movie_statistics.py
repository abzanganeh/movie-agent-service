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
    stat_type: Literal["average_rating", "count", "genre_distribution", "highest_rated", "lowest_rated", "top_rated"]
    filter_by: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional filters. For year ranges, use {'year_start': 2000, 'year_end': 2009} instead of calling multiple times. Single year: {'year': 2020}. Genre: {'genre': 'Action'}"
    )
    limit: Optional[int] = Field(
        default=10,
        ge=1,
        le=50,
        description="For top_rated stat_type: number of top-rated movies to return (default 10, max 50)"
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
        "Stat types: average_rating, count, genre_distribution, highest_rated, lowest_rated, top_rated. "
        "For year ranges (e.g., 2000s), use filter_by with 'year_start' and 'year_end' (e.g., {'year_start': 2000, 'year_end': 2009}). "
        "DO NOT call this tool multiple times for each year - use year_start/year_end for ranges. "
        "For single year, use {'year': 2020}. For genre, use {'genre': 'Action'}. "
        "highest_rated returns the movie(s) with highest rating. lowest_rated returns the movie(s) with lowest rating. "
        "top_rated returns the top N movies sorted by rating (use limit parameter, default 10). "
        "When user asks for 'top 10' or 'list top ratings', use stat_type='top_rated' with limit=10."
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
        filter_by: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 10
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
        
        if stat_type == "highest_rated":
            movies_with_ratings = [
                m for m in filtered_movies
                if m.imdb_rating is not None
            ]
            if not movies_with_ratings:
                return '{"error": "No movies with ratings found"}'
            max_rating = max(m.imdb_rating for m in movies_with_ratings)
            top_movies = [
                {"title": m.title, "year": m.year, "rating": m.imdb_rating}
                for m in movies_with_ratings
                if m.imdb_rating == max_rating
            ]
            return f'{{"highest_rating": {max_rating}, "movies": {top_movies}}}'
        
        if stat_type == "lowest_rated":
            movies_with_ratings = [
                m for m in filtered_movies
                if m.imdb_rating is not None
            ]
            if not movies_with_ratings:
                return '{"error": "No movies with ratings found"}'
            min_rating = min(m.imdb_rating for m in movies_with_ratings)
            bottom_movies = [
                {"title": m.title, "year": m.year, "rating": m.imdb_rating}
                for m in movies_with_ratings
                if m.imdb_rating == min_rating
            ]
            return f'{{"lowest_rating": {min_rating}, "movies": {bottom_movies}}}'
        
        if stat_type == "top_rated":
            movies_with_ratings = [
                m for m in filtered_movies
                if m.imdb_rating is not None
            ]
            if not movies_with_ratings:
                return '{"error": "No movies with ratings found"}'
            # Sort by rating (descending) and take top N
            sorted_movies = sorted(
                movies_with_ratings,
                key=lambda m: m.imdb_rating,
                reverse=True
            )
            top_n = sorted_movies[:limit]
            top_movies = [
                {"title": m.title, "year": m.year, "rating": m.imdb_rating}
                for m in top_n
            ]
            return f'{{"top_rated": {top_movies}, "count": {len(top_movies)}, "limit": {limit}}}'
        
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
        
        # Filter by year (single year)
        if "year" in filter_by:
            year = filter_by["year"]
            filtered = [m for m in filtered if m.year == year]
        
        # Filter by year range (for decades like 2000s)
        if "year_start" in filter_by or "year_end" in filter_by:
            year_start = filter_by.get("year_start")
            year_end = filter_by.get("year_end")
            if year_start is not None and year_end is not None:
                filtered = [m for m in filtered if m.year is not None and year_start <= m.year <= year_end]
            elif year_start is not None:
                filtered = [m for m in filtered if m.year is not None and m.year >= year_start]
            elif year_end is not None:
                filtered = [m for m in filtered if m.year is not None and m.year <= year_end]
        
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
        filter_by: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 10
    ) -> str:
        """Async version of _run."""
        return self._run(stat_type, filter_by, limit)

