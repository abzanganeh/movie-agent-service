from typing import List
from langchain_core.documents import Document
from src.movie_agent.tools.impl import MovieSearchTool, PosterAnalysisTool
from src.movie_agent.schemas import PosterAnalysisResponse

class DummyRetriever:
    """Dummy retriever for Step K evaluation."""
    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        return [
            Document(page_content=f"Dummy result for '{query}'",
                     metadata={"title": f"DummyMovie{i}", "year": 2026})
            for i in range(k)
        ]

class DummyVisionTool:
    """Dummy vision tool for Step K evaluation."""
    def analyze_poster(self, image_path: str) -> PosterAnalysisResponse:
        return PosterAnalysisResponse(
            inferred_genres=["Sci-Fi", "Action"],
            mood="Exciting",
            confidence=0.95
        )

# LangChain adapter wrappers
class EvalMovieSearchTool(MovieSearchTool):
    def __init__(self):
        super().__init__(retriever=DummyRetriever(), top_k=3)

class EvalPosterAnalysisTool(PosterAnalysisTool):
    def __init__(self):
        super().__init__(vision_tool=DummyVisionTool())
