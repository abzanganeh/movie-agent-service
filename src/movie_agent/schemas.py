from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ChatResponse:
    answer: str
    movies: List[str]
    reasoning_type: str
    latency_ms: Optional[int] = None
    
    
@dataclass
class PosterAnalysisResponse:
    inferred_genres: List[str]
    mood: str
    confidence: float