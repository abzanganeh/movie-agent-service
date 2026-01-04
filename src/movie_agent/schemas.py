from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ChatResponse:
    answer: str
    movies: List[str]
    reasoning_type: str
    tools_used: List[str]
    llm_latency_ms: Optional[int] = None
    tool_latency_ms: Optional[int] = None
    latency_ms: Optional[int] = None
    resolution_metadata: Optional[Dict[str, Any]] = None
    
    
@dataclass
class PosterAnalysisResponse:
    inferred_genres: List[str]
    mood: str
    confidence: float
    title: Optional[str] = None