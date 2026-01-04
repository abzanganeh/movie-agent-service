"""
Core abstractions for semantic resolution.

Defines the protocol and result types for entity normalization.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class ResolutionResult:
    """
    Immutable result of semantic resolution.
    
    Attributes:
        canonical_value: The resolved canonical entity (e.g., "Inception")
        confidence: Confidence score between 0.0 and 1.0
        strategy_used: Name of the matching strategy used (e.g., "exact", "fuzzy")
        original_query: The original query that was resolved
    """
    canonical_value: Optional[str]
    confidence: float
    strategy_used: str
    original_query: str
    
    def is_confident(self, threshold: float = 0.75) -> bool:
        """Check if resolution confidence meets threshold."""
        return self.confidence >= threshold
    
    def __post_init__(self):
        """Validate confidence score."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


class SemanticResolver(ABC):
    """
    Protocol for semantic resolution strategies.
    
    Converts ambiguous user signals into canonical domain entities.
    Used for:
    - Entity normalization ("LOTR" → "The Lord of the Rings")
    - Typo correction ("Inceptoin" → "Inception")
    - Intent rescue (anchor entities in mixed results)
    - Title inference (vision caption → movie title)
    """
    
    @abstractmethod
    def resolve(
        self,
        query: str,
        candidates: List[str],
    ) -> ResolutionResult:
        """
        Resolve a query against candidate entities.
        
        :param query: The ambiguous query to resolve
        :param candidates: List of candidate canonical entities
        :return: ResolutionResult with canonical value and confidence
        """
        pass

