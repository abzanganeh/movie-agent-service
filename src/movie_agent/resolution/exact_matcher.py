"""
Exact matching strategy for semantic resolution.

Fast, deterministic matching for exact entity matches.
"""
from typing import List, Optional
from .semantic_resolver import SemanticResolver, ResolutionResult


class ExactTitleMatcher(SemanticResolver):
    """
    Exact match strategy for entity resolution.
    
    Fast, deterministic matching. Used as first strategy in escalation.
    Case-insensitive matching.
    """
    
    def resolve(
        self,
        query: str,
        candidates: List[str],
    ) -> ResolutionResult:
        """
        Find exact match (case-insensitive) in candidates.
        
        :param query: Query to match
        :param candidates: List of candidate entities
        :return: ResolutionResult with exact match or None
        """
        query_normalized = query.strip().lower()
        
        for candidate in candidates:
            if candidate.strip().lower() == query_normalized:
                return ResolutionResult(
                    canonical_value=candidate,
                    confidence=1.0,
                    strategy_used="exact",
                    original_query=query,
                )
        
        # No exact match found
        return ResolutionResult(
            canonical_value=None,
            confidence=0.0,
            strategy_used="exact",
            original_query=query,
        )

