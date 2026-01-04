from typing import Optional, List
from time import time

from .config import MovieAgentConfig
from .exceptions import AgentNotInitializedError, VisionAnalystNotInitializedError
from .schemas import ChatResponse, PosterAnalysisResponse
from .tools import (
    RetrieverTool,
    VisionTool,
    GenerateMovieQuizTool,
    CheckQuizAnswerTool,
    CompareMoviesTool,
    SearchActorTool,
    SearchDirectorTool,
    SearchYearTool,
)
from langchain_core.documents import Document
from .agent.tool_calling_agent import ToolCallingAgent
from .agent.prompts import MOVIE_REACT_PROMPT
from langchain.memory import ConversationBufferMemory
from .tools.impl import MovieSearchTool, PosterAnalysisTool


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

    def warmup(self) -> None:
        """
        Preload heavy resources (models, vector store, etc.).
        Cold-start mitigation hook.
        """
        if self._agent:
            return

        if not self._vector_store:
            raise RuntimeError("Retriever tool must be injected before warmup.")

        tools = []

        search_tool = MovieSearchTool(retriever=self._vector_store)
        tools.append(search_tool)

        # Optional capability expansion tools (Colab parity)
        tools.append(GenerateMovieQuizTool(retriever=self._vector_store))
        tools.append(CheckQuizAnswerTool())
        tools.append(CompareMoviesTool(retriever=self._vector_store))
        tools.append(SearchActorTool(retriever=self._vector_store))
        tools.append(SearchDirectorTool(retriever=self._vector_store))
        tools.append(SearchYearTool(retriever=self._vector_store))

        if self.config.enable_vision:
            if not self._vision_analyst:
                raise RuntimeError("Vision tool must be injected when enable_vision=True.")
            # If the vision tool supports retrieval-backed title inference, inject the retriever.
            if hasattr(self._vision_analyst, "_retriever") and getattr(self._vision_analyst, "_retriever") is None:
                setattr(self._vision_analyst, "_retriever", self._vector_store)
            vision_tool = PosterAnalysisTool(vision_tool=self._vision_analyst)
            tools.append(vision_tool)

        # Create prompt with tool names
        prompt = MOVIE_REACT_PROMPT.partial(tool_names=[t.name for t in tools])
        
        self._agent = ToolCallingAgent(
            llm=self.config.llm,
            tools=tools,
            prompt=prompt,
            verbose=self.config.verbose,
        )


    # Query handling
    def chat(self, user_message: str) -> ChatResponse:
        if not self._agent:
            raise AgentNotInitializedError("Agent is not initialized.")

        start_time = time()
        result = self._agent.run(user_message)
        total_latency_ms = int((time() - start_time) * 1000)

        # Extract precise latency breakdown from agent result
        # Tool latency is now tracked via LangChain callbacks
        llm_latency = result.get("llm_latency_ms")
        tool_latency = result.get("tool_latency_ms")

        return ChatResponse(
            answer=result["answer"],
            movies=result["movies"],
            tools_used=result.get("tools_used", []),
            llm_latency_ms=llm_latency,
            tool_latency_ms=tool_latency,
            latency_ms=total_latency_ms,
            reasoning_type="tool_calling",
        )


    # Poster / Vision analysis
    def analyze_poster(self, image_path: str) -> PosterAnalysisResponse:
        """
        Analyze a movie poster and infer metadata using the vision analyst tool.
        """
        if not self._vision_analyst:
            raise VisionAnalystNotInitializedError("Vision analyst is not initialized.")

        return self._vision_analyst.analyze_poster(image_path)

    # Dependency injection setters
    def set_vector_store(self, vector_store: RetrieverTool) -> None:
        """Inject a retrieval tool."""
        self._vector_store = vector_store

    def set_vision_analyst(self, vision_tool: VisionTool) -> None:
        """Inject a vision analysis tool."""
        self._vision_analyst = vision_tool