"""
Semantic resolution layer for entity normalization and typo correction.

This module provides a dedicated abstraction for converting ambiguous user signals
into canonical domain entities (movie titles, directors, actors).

Key components:
- SemanticResolver: Protocol for resolution strategies
- ResolutionResult: Immutable result with confidence scoring
- Matchers: Exact, Fuzzy, and future Embedding strategies
- ResolutionPolicy: Escalation logic for matcher strategies
"""
from .semantic_resolver import SemanticResolver, ResolutionResult
from .exact_matcher import ExactTitleMatcher
from .fuzzy_matcher import FuzzyTitleMatcher
from .resolution_policy import ResolutionPolicy
from .movie_title_resolver import MovieTitleResolver
from .vocabulary_builder import VocabularyBuilder
from .resolver_factory import create_title_resolver
from .entity_extractor import EntityExtractor, ExtractedEntity
from .resolution_metadata import ResolutionMetadata

__all__ = [
    "SemanticResolver",
    "ResolutionResult",
    "ExactTitleMatcher",
    "FuzzyTitleMatcher",
    "ResolutionPolicy",
    "MovieTitleResolver",
    "VocabularyBuilder",
    "create_title_resolver",
    "EntityExtractor",
    "ExtractedEntity",
    "ResolutionMetadata",
]

