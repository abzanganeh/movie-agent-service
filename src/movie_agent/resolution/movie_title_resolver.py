"""
Concrete implementation of semantic resolver for movie titles.

Combines matchers and policy into a complete resolution system.
"""
from typing import List, Optional
from .semantic_resolver import SemanticResolver, ResolutionResult
from .exact_matcher import ExactTitleMatcher
from .fuzzy_matcher import FuzzyTitleMatcher
from .resolution_policy import ResolutionPolicy
from .vocabulary_builder import VocabularyBuilder


class MovieTitleResolver(SemanticResolver):
    """
    Concrete resolver for movie title resolution.
    
    Combines:
    - ExactTitleMatcher (fast, deterministic)
    - FuzzyTitleMatcher (handles typos, partial matches)
    - ResolutionPolicy (escalation logic)
    
    Usage:
        resolver = MovieTitleResolver(vocabulary_builder)
        result = resolver.resolve("Inceptoin", candidates)
        if result.is_confident():
            canonical_title = result.canonical_value  # "Inception"
    """
    
    def __init__(
        self,
        vocabulary_builder: VocabularyBuilder,
        fuzzy_threshold: float = 0.75,
        confidence_threshold: float = 0.75,
    ):
        """
        Initialize movie title resolver.
        
        :param vocabulary_builder: VocabularyBuilder with movie data
        :param fuzzy_threshold: Minimum score for fuzzy matches (0.0-1.0)
        :param confidence_threshold: Minimum confidence to accept resolution (0.0-1.0)
        """
        self._vocabulary = vocabulary_builder
        
        # Create matchers
        exact_matcher = ExactTitleMatcher()
        fuzzy_matcher = FuzzyTitleMatcher(threshold=fuzzy_threshold)
        
        # Create policy with escalation order
        self._policy = ResolutionPolicy(
            matchers=[exact_matcher, fuzzy_matcher],
            confidence_threshold=confidence_threshold,
        )
    
    def resolve(
        self,
        query: str,
        candidates: Optional[List[str]] = None,
    ) -> ResolutionResult:
        """
        Resolve movie title query.
        
        :param query: Query to resolve (e.g., "Inceptoin", "LOTR")
        :param candidates: Optional custom candidate list. If None, uses vocabulary titles
        :return: ResolutionResult with canonical title and confidence
        """
        if candidates is None:
            candidates = self._vocabulary.get_title_candidates()
        
        return self._policy.resolve(query, candidates)
    
    def resolve_multiple(
        self,
        queries: List[str],
    ) -> List[ResolutionResult]:
        """
        Resolve multiple queries in batch.
        
        :param queries: List of queries to resolve
        :return: List of ResolutionResults
        """
        return [self.resolve(query) for query in queries]

