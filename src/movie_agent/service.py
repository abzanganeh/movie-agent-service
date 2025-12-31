from typing import Optional, List
from time import time

from .config import MovieAgentConfig
from .exceptions import AgentNotInitializedError, VisionAnalystNotInitializedError
from .schemas import ChatResponse, PosterAnalysisResponse
from .tools import RetrieverTool, VisionTool
from langchain_core.documents import Document


class MovieAgentService:
    """
    Facade over the movie AI agent subsystem.
    The ONLY entry point for the UI layers.
    """

    def __init__(self, config: MovieAgentConfig):
        """
        Composition root.
        All dependencies (tools, agent) are created and wired here.
        """
        self.config = config

        # Internal components (initialized later)
        self._agent: Optional[object] = None
        self._vector_store: Optional[RetrieverTool] = None
        self._vision_analyst: Optional[VisionTool] = None

        if self.config.warmup_on_start:
            self.warmup()

    # ----------------------------
    # Cold-start / Warmup
    # ----------------------------
    def warmup(self) -> None:
        """
        Preload heavy resources (models, vector store, etc.).
        Cold-start mitigation hook.
        """
        # Placeholders for actual initialization
        self._agent = "Initialized"
        return None

    # ----------------------------
    # Query handling
    # ----------------------------
    def chat(self, user_message: str) -> ChatResponse:
        """
        Process a user query and return a structured response.
        Orchestrates retrieval and agent reasoning.
        """
        if not self._agent:
            raise AgentNotInitializedError("Agent is not initialized.")

        start_time = time()

        # Step 1: Retrieve candidate documents if vector store exists
        movies: List[Document] = []
        if self._vector_store:
            movies = self._vector_store.retrieve(user_message, k=5)

        # Step 2: Placeholder for actual agent reasoning (ReAct / LLM)
        answer = "Agent logic not implemented yet."
        reasoning_type = "skeleton"

        latency_ms = int((time() - start_time) * 1000)

        return ChatResponse(
            answer=answer,
            movies=movies,
            latency_ms=latency_ms,
            reasoning_type=reasoning_type
        )

    # ----------------------------
    # Poster / Vision analysis
    # ----------------------------
    def analyze_poster(self, image_path: str) -> PosterAnalysisResponse:
        """
        Analyze a movie poster and infer metadata using the vision analyst tool.
        """
        if not self._vision_analyst:
            raise VisionAnalystNotInitializedError("Vision analyst is not initialized.")

        return self._vision_analyst.analyze_poster(image_path)

    # ----------------------------
    # Dependency injection setters
    # ----------------------------
    def set_vector_store(self, vector_store: RetrieverTool) -> None:
        """Inject a retrieval tool."""
        self._vector_store = vector_store

    def set_vision_analyst(self, vision_tool: VisionTool) -> None:
        """Inject a vision analysis tool."""
        self._vision_analyst = vision_tool