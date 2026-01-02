from typing import List, Optional
from langchain.tools import BaseTool
from langchain_core.documents import Document
from .retriever_tool import RetrieverTool
from .vision_tool import VisionTool
from ..schemas import PosterAnalysisResponse


class MovieSearchTool(BaseTool):
    """
    LangChain adapter for the RetrieverTool protocol.
    Exposes movie semantic search to the ReAct agent.
    """

    name = "movie_search"
    description = (
        "Use this tool to find movies by description, title, or attributes. "
        "Input should be a natural language query."
    )

    def __init__(self, retriever: RetrieverTool, top_k: int = 5):
        self.retriever = retriever
        self.top_k = top_k

    def _run(self, query: str) -> str:
        # Synchronous execution
        results: List[Document] = self.retriever.retrieve(query, k=self.top_k)
        if not results:
            return "No movies found matching the query."
        # Concatenate titles and short metadata
        summaries = [
            f"{doc.metadata.get('title', 'Unknown')} ({doc.metadata.get('year', 'N/A')})"
            for doc in results
        ]
        return "; ".join(summaries)

    async def _arun(self, query: str) -> str:
        # Async LangChain support
        return self._run(query)


class PosterAnalysisTool(BaseTool):
    """
    LangChain adapter for the VisionTool protocol.
    Exposes poster-based genre/mood inference to the ReAct agent.
    """

    name = "analyze_movie_poster"
    description = (
        "Use this tool when the user provides a movie poster image. "
        "Input should be a valid image path. Returns inferred genres, mood, and confidence."
    )

    def __init__(self, vision_tool: VisionTool):
        self.vision_tool = vision_tool

    def _run(self, image_path: str) -> str:
        try:
            response: PosterAnalysisResponse = self.vision_tool.analyze_poster(image_path)
            genres = ", ".join(response.inferred_genres)
            return (
                f"Genres: {genres}. Mood: {response.mood}. "
                f"Confidence: {response.confidence:.2f}"
            )
        except Exception as e:
            return f"Failed to analyze poster: {str(e)}"

    async def _arun(self, image_path: str) -> str:
        return self._run(image_path)
