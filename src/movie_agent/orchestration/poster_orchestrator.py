"""
Poster orchestrator - write path.

Handles poster analysis and writes to SessionContext.
"""
from typing import Optional
from ..tools.vision_tool import VisionTool
from ..tools.movie_retriever import MovieRetriever
from ..schemas import PosterAnalysisResponse
from ..context.session_context import PosterContext, SessionContext
from .poster_orchestration import PosterOrchestrationService


class PosterOrchestrator:
    """
    Orchestrates poster analysis and writes to SessionContext.
    
    Write path: image → analysis → SessionContext
    """
    
    def __init__(
        self,
        vision_tool: VisionTool,
        retriever: MovieRetriever,
    ):
        """
        Initialize poster orchestrator.
        
        :param vision_tool: VisionTool instance
        :param retriever: MovieRetriever instance
        """
        self._orchestration_service = PosterOrchestrationService(
            vision_tool=vision_tool,
            retriever=retriever,
        )
    
    def analyze_and_store(
        self,
        image_path: str,
        session_context: SessionContext
    ) -> PosterContext:
        """
        Analyze poster and store result in session context.
        
        :param image_path: Path to poster image
        :param session_context: SessionContext to write to
        :return: PosterContext with analysis results
        """
        response = self._orchestration_service.analyze(image_path)
        
        poster_context = PosterContext(
            caption=response.caption,
            title=response.title,
            mood=response.mood,
            confidence=response.confidence,
            inferred_genres=response.inferred_genres,
        )
        
        session_context.poster = poster_context
        
        return poster_context

