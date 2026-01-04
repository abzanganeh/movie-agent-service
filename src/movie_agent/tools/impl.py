from typing import List, Optional, Any
from pydantic import Field, BaseModel
from langchain.tools import BaseTool
from langchain_core.documents import Document
from .retriever_tool import RetrieverTool
from .vision_tool import VisionTool
from ..schemas import PosterAnalysisResponse


class MovieSearchArgs(BaseModel):
    query: str


class MovieSearchTool(BaseTool):
    """
    LangChain adapter for the RetrieverTool protocol.
    Exposes movie semantic search to the ReAct agent.
    """

    name: str = "movie_search"
    description: str = (
        "Use this tool to find movies by description, title, or attributes. "
        "Input should be a natural language query."
    )
    # Pydantic v2 requires declared fields for assignment
    retriever: Any = Field(default=None)
    top_k: int = Field(default=5)

    def __init__(self, retriever, top_k: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.retriever = retriever
        self.top_k = int(top_k)
    
    args_schema: type[BaseModel] = MovieSearchArgs

    def _run(self, query: str) -> str:
        results: List[Document] = self.retriever.retrieve(query, k=self.top_k)
        if not results:
            return "No movies found matching the query."
        summaries = [
            f"{doc.metadata.get('title', 'Unknown')} ({doc.metadata.get('year', 'N/A')})"
            for doc in results
        ]
        return "; ".join(summaries)
    
    def get_last_resolution_metadata(self):
        """Get resolution metadata from the last retrieve() call."""
        if hasattr(self.retriever, 'get_last_resolution_metadata'):
            return self.retriever.get_last_resolution_metadata()
        return None

    async def _arun(self, query: str) -> str:
        return self._run(query)


class PosterAnalysisArgs(BaseModel):
    image_path: str


class PosterAnalysisTool(BaseTool):
    name: str = "analyze_movie_poster"
    description: str = (
        "Use this tool when the user provides a movie poster image. "
        "Input should be a valid image path. Returns inferred genres, mood, and confidence."
    )
    vision_tool: Any = Field(default=None)

    args_schema: type[BaseModel] = PosterAnalysisArgs

    def _run(self, image_path: str) -> str:
        try:
            response: PosterAnalysisResponse = self.vision_tool.analyze_poster(image_path)
            title = response.title or "Unknown"
            genres = ", ".join(response.inferred_genres)
            return (
                f"Title: {title}. Genres: {genres}. Mood: {response.mood}. "
                f"Confidence: {response.confidence:.2f}"
            )
        except Exception as e:
            return f"Failed to analyze poster: {str(e)}"

    async def _arun(self, image_path: str) -> str:
        return self._run(image_path)
