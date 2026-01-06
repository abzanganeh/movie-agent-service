"""
Resolution metadata for tracking query resolution.

Used to expose resolution information in responses for explainability.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ResolutionMetadata:
    """
    Metadata about query resolution for explainability.
    
    Tracks:
    - Which entities were resolved
    - Resolution strategy used
    - Confidence scores
    - Original vs resolved queries
    """
    original_query: str
    resolved_query: str
    resolution_strategy: Optional[str] = None
    resolution_confidence: Optional[float] = None
    entities_resolved: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
            "original_query": self.original_query,
            "resolved_query": self.resolved_query,
        }
        
        if self.resolution_strategy:
            result["resolution_strategy"] = self.resolution_strategy
        
        if self.resolution_confidence is not None:
            result["resolution_confidence"] = self.resolution_confidence
        
        if self.entities_resolved:
            result["entities_resolved"] = self.entities_resolved
        
        return result

