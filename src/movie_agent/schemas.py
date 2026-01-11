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
    confidence: Optional[float] = None  # Confidence score from agent (0.0-1.0)
    # Poster analysis fields (None if not poster analysis)
    title: Optional[str] = None  # Identified movie title (poster analysis)
    mood: Optional[str] = None   # Synthesized mood (poster analysis)
    caption: Optional[str] = None  # Vision tool caption (poster analysis)
    # Quiz fields (None if not quiz-related)
    quiz_data: Optional[Dict[str, Any]] = None  # Structured quiz data (question, options, progress) - NO ANSWERS
    
    
@dataclass
class PosterAnalysisResponse:
    caption: str  # Visual description (evidence) from vision tool
    title: Optional[str] = None  # Identified movie title from retriever (orchestration service's responsibility)
    mood: str = "Neutral"  # Synthesized mood (orchestration service's responsibility)
    confidence: float = 0.0  # Confidence score (orchestration service's responsibility)
    inferred_genres: List[str] = field(default_factory=list)  # Genres inferred by vision tool