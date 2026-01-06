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
    Exposes movie semantic search to the tool-calling agent.
    """

    name: str = "movie_search"
    description: str = (
        "Use this tool to find, search, or discover movies by description, genre, year, title, or attributes. "
        "Use for: 'find comedies', 'show me action movies', 'recommend sci-fi', 'movies from 90s', etc. "
        "Input should be a natural language query describing what movies to find."
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
        "Input should be a valid image path. Returns a visual description (caption) "
        "that you can use as a search query with movie_search to identify the movie."
    )
    vision_tool: Any = Field(default=None)

    args_schema: type[BaseModel] = PosterAnalysisArgs

    def _run(self, image_path: str) -> str:
        """
        Analyze poster and return caption as evidence.
        
        The agent should then call movie_search with this caption
        to identify the movie via semantic search.
        """
        try:
            response: PosterAnalysisResponse = self.vision_tool.analyze_poster(image_path)
            # Return the caption as evidence - agent will use it for movie_search
            # Format matches Colab approach: "Vision analysis says: '{caption}'"
            return (
                f"User uploaded a movie poster. Vision analysis says: '{response.caption}'. "
                f"Please search for movies that match this description using movie_search."
            )
        except Exception as e:
            return f"Failed to analyze poster: {str(e)}"

    async def _arun(self, image_path: str) -> str:
        return self._run(image_path)
