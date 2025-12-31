import pytest
from src.movie_agent.service import MovieAgentService, RetrieverTool, VisionTool
from src.movie_agent.config import MovieAgentConfig
from src.movie_agent.schemas import PosterAnalysisResponse
from langchain_core.documents import Document


class FakeRetriever(RetrieverTool):
    def retrieve(self, query: str, k: int = 5):
        return [Document(page_content="Title: Fake Movie", metadata={"title": "Fake Movie"})]


class FakeVision(VisionTool):
    def analyze_poster(self, image_path: str) -> PosterAnalysisResponse:
        return PosterAnalysisResponse(
            inferred_genres=["Action", "Thriller"],
            mood="suspenseful",
            confidence=0.85
        )


def test_agent_service_orchestration():
    # Create config
    config = MovieAgentConfig(
        movies_csv_path="dummy_path.csv",
        warmup_on_start=False  # Skip warmup in tests
    )
    
    # Create service with config
    agent = MovieAgentService(config)
    
    # Inject tools using dependency injection
    retriever = FakeRetriever()
    vision = FakeVision()
    agent.set_vector_store(retriever)
    agent.set_vision_analyst(vision)
    
    # Initialize agent (warmup sets _agent to initialized state)
    agent.warmup()
    
    # Test chat method
    response = agent.chat("test query")
    assert response.answer == "Agent logic not implemented yet."
    assert len(response.movies) > 0  # Should have retrieved documents
    assert response.reasoning_type == "skeleton"
    assert response.latency_ms is not None
    
    # Test vision analysis
    poster_response = agent.analyze_poster("dummy_poster.jpg")
    assert poster_response.mood == "suspenseful"
    assert poster_response.confidence == 0.85
    assert "Action" in poster_response.inferred_genres
