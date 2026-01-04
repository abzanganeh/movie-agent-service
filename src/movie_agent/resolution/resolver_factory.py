"""
Factory for creating semantic resolvers.

Builds vocabulary from dataset and creates configured resolvers.
"""
from typing import Optional
from .vocabulary_builder import VocabularyBuilder
from .movie_title_resolver import MovieTitleResolver
from ..config import MovieAgentConfig
from ..data_loader import MovieDataLoader


def create_title_resolver(
    config: Optional[MovieAgentConfig] = None,
    vocabulary_builder: Optional[VocabularyBuilder] = None,
) -> Optional[MovieTitleResolver]:
    """
    Factory function to create a MovieTitleResolver.
    
    Builds vocabulary from dataset if not provided.
    Returns None if fuzzy matching is disabled in config.
    
    :param config: MovieAgentConfig instance
    :param vocabulary_builder: Optional pre-built VocabularyBuilder
    :return: MovieTitleResolver if enabled, None otherwise
    """
    if config is None or not config.enable_fuzzy_matching:
        return None
    
    # Build vocabulary if not provided
    if vocabulary_builder is None:
        if not config.movies_csv_path:
            # Cannot build vocabulary without movies data
            return None
        
        loader = MovieDataLoader(config.movies_csv_path)
        movies = loader.load_movies()
        vocabulary_builder = VocabularyBuilder(movies)
    
    # Create resolver with config thresholds
    return MovieTitleResolver(
        vocabulary_builder=vocabulary_builder,
        fuzzy_threshold=config.fuzzy_threshold,
        confidence_threshold=config.resolution_confidence_threshold,
    )

