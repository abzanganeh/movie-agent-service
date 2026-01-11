"""
Fuzzy matching strategy for semantic resolution using rapidfuzz.

Handles typos, partial matches, and near-misses.
"""
from typing import List, Optional
from rapidfuzz import fuzz, process

from .semantic_resolver import SemanticResolver, ResolutionResult


class FuzzyTitleMatcher(SemanticResolver):
    """
    Fuzzy match strategy using rapidfuzz.
    
    Handles:
    - Typos ("Inceptoin" → "Inception")
    - Partial matches ("Lord Rings" → "The Lord of the Rings")
    - Abbreviations ("LOTR" → "The Lord of the Rings")
    
    Uses rapidfuzz's process.extractOne for best match finding.
    """
    
    def __init__(
        self,
        threshold: float = 0.75,
        scorer: str = "ratio",
    ):
        """
        Initialize fuzzy matcher.
        
        :param threshold: Minimum confidence score to accept a match (0.0-1.0)
        :param scorer: rapidfuzz scorer to use ("ratio", "partial_ratio", "token_sort_ratio")
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")
        
        self.threshold = threshold
        self.scorer = scorer
        
        # Map scorer names to rapidfuzz functions
        self._scorer_map = {
            "ratio": fuzz.ratio,
            "partial_ratio": fuzz.partial_ratio,
            "token_sort_ratio": fuzz.token_sort_ratio,
            "token_set_ratio": fuzz.token_set_ratio,
        }
        
        if scorer not in self._scorer_map:
            raise ValueError(
                f"Unknown scorer '{scorer}'. "
                f"Must be one of: {list(self._scorer_map.keys())}"
            )
    
    def resolve(
        self,
        query: str,
        candidates: List[str],
    ) -> ResolutionResult:
        """
        Find best fuzzy match in candidates using rapidfuzz.
        
        :param query: Query to match
        :param candidates: List of candidate entities
        :return: ResolutionResult with best match if above threshold
        """
        if not candidates:
            return ResolutionResult(
                canonical_value=None,
                confidence=0.0,
                strategy_used="fuzzy",
                original_query=query,
            )
        
        # Use rapidfuzz process.extractOne for best match
        scorer_func = self._scorer_map[self.scorer]
        
        try:
            result = process.extractOne(
                query,
                candidates,
                scorer=scorer_func,
            )
            
            if result:
                matched_value, score, _ = result
                # Convert score (0-100) to confidence (0.0-1.0)
                confidence = score / 100.0
                
                if confidence >= self.threshold:
                    return ResolutionResult(
                        canonical_value=matched_value,
                        confidence=confidence,
                        strategy_used="fuzzy",
                        original_query=query,
                    )
        except Exception:
            # If rapidfuzz fails, return no match
            pass
        
        # No match above threshold
        return ResolutionResult(
            canonical_value=None,
            confidence=0.0,
            strategy_used="fuzzy",
            original_query=query,
        )

