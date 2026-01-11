"""
Resolution policy for matcher escalation.

Implements the escalation logic: exact → fuzzy → embedding (future).
"""
from typing import List, Optional
from .semantic_resolver import SemanticResolver, ResolutionResult


class ResolutionPolicy:
    """
    Policy for escalating through multiple matching strategies.
    
    Tries matchers in order until one returns a confident result.
    This provides predictable, testable escalation behavior.
    """
    
    def __init__(
        self,
        matchers: List[SemanticResolver],
        confidence_threshold: float = 0.75,
    ):
        """
        Initialize resolution policy.
        
        :param matchers: List of matchers to try in order (e.g., [ExactMatcher, FuzzyMatcher])
        :param confidence_threshold: Minimum confidence to accept a match
        """
        if not matchers:
            raise ValueError("At least one matcher must be provided")
        
        self._matchers = matchers
        self.confidence_threshold = confidence_threshold
    
    def resolve(
        self,
        query: str,
        candidates: List[str],
    ) -> ResolutionResult:
        """
        Resolve query by trying matchers in order.
        
        Escalation logic:
        1. Try first matcher (usually ExactMatcher)
        2. If confidence >= threshold, return result
        3. Try next matcher (usually FuzzyMatcher)
        4. If confidence >= threshold, return result
        5. Continue until all matchers tried
        6. Return best result (highest confidence) or None if all below threshold
        
        :param query: Query to resolve
        :param candidates: List of candidate entities
        :return: ResolutionResult with best match or None
        """
        best_result: Optional[ResolutionResult] = None
        
        for matcher in self._matchers:
            result = matcher.resolve(query, candidates)
            
            # If this result meets threshold, return immediately (fast path)
            if result.is_confident(self.confidence_threshold):
                return result
            
            # Track best result so far (for fallback)
            if best_result is None or result.confidence > best_result.confidence:
                best_result = result
        
        # Return best result found (even if below threshold)
        # This allows caller to decide what to do with low-confidence matches
        if best_result:
            return best_result
        
        # No matcher found anything
        return ResolutionResult(
            canonical_value=None,
            confidence=0.0,
            strategy_used="none",
            original_query=query,
        )

