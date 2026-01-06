"""
Vocabulary builder for semantic resolution.

Builds vocabulary of canonical entities from movie dataset.
"""
from typing import List, Set
from ..models import Movie


class VocabularyBuilder:
    """
    Builds vocabulary of canonical entities from movie data.
    
    Extracts:
    - Movie titles
    - Director names
    - Actor names (from stars)
    
    Used to build candidate lists for semantic resolution.
    """
    
    def __init__(self, movies: List[Movie]):
        """
        Initialize vocabulary builder with movies.
        
        :param movies: List of Movie objects to build vocabulary from
        """
        self._movies = movies
        self._titles: Set[str] = set()
        self._directors: Set[str] = set()
        self._actors: Set[str] = set()
        
        self._build_vocabulary()
    
    def _build_vocabulary(self):
        """Build vocabulary sets from movies."""
        for movie in self._movies:
            # Add title
            if movie.title:
                self._titles.add(movie.title)
            
            # Add director
            if movie.director:
                self._directors.add(movie.director)
            
            # Add actors
            if movie.stars:
                self._actors.update(movie.stars)
    
    def get_titles(self) -> List[str]:
        """Get list of all movie titles."""
        return sorted(list(self._titles))
    
    def get_directors(self) -> List[str]:
        """Get list of all director names."""
        return sorted(list(self._directors))
    
    def get_actors(self) -> List[str]:
        """Get list of all actor names."""
        return sorted(list(self._actors))
    
    def get_all_entities(self) -> List[str]:
        """Get combined list of all entities (titles + directors + actors)."""
        return self.get_titles() + self.get_directors() + self.get_actors()
    
    def get_title_candidates(self) -> List[str]:
        """Get candidates for title resolution (titles only)."""
        return self.get_titles()

