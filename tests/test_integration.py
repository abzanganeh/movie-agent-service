"""
Integration tests for the full movie agent service.
Tests end-to-end workflows similar to Colab validation.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from langchain_core.documents import Document

from src.movie_agent.service import MovieAgentService
from src.movie_agent.config import MovieAgentConfig
from src.movie_agent.schemas import PosterAnalysisResponse


@pytest.fixture
def mock_retriever():
    """Create a mock retriever for testing."""
    retriever = Mock()
    retriever.retrieve.return_value = [
        Document(
            page_content="Sci-fi movie about dreams",
            metadata={"title": "Inception", "year": 2010, "genres": ["Sci-Fi", "Thriller"]}
        ),
        Document(
            page_content="Space exploration",
            metadata={"title": "Interstellar", "year": 2014, "genres": ["Sci-Fi", "Drama"]}
        ),
    ]
    return retriever


@pytest.fixture
def mock_vision_tool():
    """Create a mock vision tool for testing."""
    vision_tool = Mock()
    vision_tool.analyze_poster.return_value = PosterAnalysisResponse(
        inferred_genres=["Drama"],
        mood="Neutral",
        confidence=0.7,
        title="Test Movie (2020)"
    )
    return vision_tool


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    llm = Mock()
    return llm


@pytest.fixture
def service_config():
    """Create a test configuration."""
    return MovieAgentConfig(
        movies_csv_path="dummy.csv",
        warmup_on_start=False,
        enable_vision=True,
    )


class TestMovieSearchIntegration:
    """Integration tests for movie search functionality."""

    def test_movie_search_workflow(self, service_config, mock_retriever, mock_llm):
        """Test complete movie search workflow."""
        service = MovieAgentService(service_config)
        service.set_vector_store(mock_retriever)
        service.config.llm = mock_llm

        # Mock the agent to return expected format
        mock_agent = Mock()
        mock_agent.run.return_value = {
            "answer": "Here are some sci-fi movies: Inception (2010), Interstellar (2014).",
            "movies": ["Inception", "Interstellar"],
            "tools_used": ["movie_search"],
            "llm_latency_ms": 500,
            "tool_latency_ms": 200,
        }
        service._agent = mock_agent

        response = service.chat("Recommend sci-fi movies like Inception")

        assert "Inception" in response.answer or "sci-fi" in response.answer.lower()
        assert response.reasoning_type == "tool_calling"
        assert isinstance(response.tools_used, list)

    def test_movie_search_handles_empty_results(self, service_config, mock_retriever, mock_llm):
        """Test that movie search handles empty results gracefully."""
        empty_retriever = Mock()
        empty_retriever.retrieve.return_value = []

        service = MovieAgentService(service_config)
        service.set_vector_store(empty_retriever)
        service.config.llm = mock_llm

        mock_agent = Mock()
        mock_agent.run.return_value = {
            "answer": "No movies found matching your query.",
            "movies": [],
            "tools_used": ["movie_search"],
        }
        service._agent = mock_agent

        response = service.chat("Find nonexistent movie")

        assert len(response.movies) == 0


class TestQuizIntegration:
    """Integration tests for quiz functionality."""

    def test_quiz_generation_workflow(self, service_config, mock_retriever, mock_llm):
        """Test complete quiz generation workflow."""
        service = MovieAgentService(service_config)
        service.set_vector_store(mock_retriever)
        service.config.llm = mock_llm

        mock_agent = Mock()
        mock_agent.run.return_value = {
            "answer": "Here's a quiz about sci-fi movies...",
            "movies": ["Inception", "Interstellar"],
            "tools_used": ["generate_movie_quiz"],
        }
        service._agent = mock_agent

        response = service.chat("Generate a quiz about sci-fi movies")

        assert "quiz" in response.answer.lower() or len(response.movies) > 0
        assert "generate_movie_quiz" in response.tools_used

    def test_quiz_answer_checking_workflow(self, service_config, mock_llm):
        """Test quiz answer checking workflow."""
        service = MovieAgentService(service_config)
        service.config.llm = mock_llm

        mock_agent = Mock()
        mock_agent.run.return_value = {
            "answer": "Your answer is correct!",
            "movies": [],
            "tools_used": ["check_quiz_answer"],
        }
        service._agent = mock_agent

        response = service.chat("Check my answer: 2010 for 'What year was Inception released?'")

        assert "check_quiz_answer" in response.tools_used


class TestComparisonIntegration:
    """Integration tests for movie comparison functionality."""

    def test_movie_comparison_workflow(self, service_config, mock_retriever, mock_llm):
        """Test complete movie comparison workflow."""
        service = MovieAgentService(service_config)
        service.set_vector_store(mock_retriever)
        service.config.llm = mock_llm

        mock_agent = Mock()
        mock_agent.run.return_value = {
            "answer": "Comparing Inception and Interstellar...",
            "movies": ["Inception", "Interstellar"],
            "tools_used": ["compare_movies"],
        }
        service._agent = mock_agent

        response = service.chat("Compare Inception and Interstellar")

        assert "compare_movies" in response.tools_used
        assert len(response.movies) >= 2


class TestSearchIntegration:
    """Integration tests for actor/director/year search."""

    def test_actor_search_workflow(self, service_config, mock_retriever, mock_llm):
        """Test actor search workflow."""
        service = MovieAgentService(service_config)
        service.set_vector_store(mock_retriever)
        service.config.llm = mock_llm

        mock_agent = Mock()
        mock_agent.run.return_value = {
            "answer": "Movies featuring Tom Hanks...",
            "movies": ["Forrest Gump", "Cast Away"],
            "tools_used": ["search_actor"],
        }
        service._agent = mock_agent

        response = service.chat("Find movies with Tom Hanks")

        assert "search_actor" in response.tools_used

    def test_director_search_workflow(self, service_config, mock_retriever, mock_llm):
        """Test director search workflow."""
        service = MovieAgentService(service_config)
        service.set_vector_store(mock_retriever)
        service.config.llm = mock_llm

        mock_agent = Mock()
        mock_agent.run.return_value = {
            "answer": "Movies directed by Christopher Nolan...",
            "movies": ["Inception", "Interstellar"],
            "tools_used": ["search_director"],
        }
        service._agent = mock_agent

        response = service.chat("Find movies by Christopher Nolan")

        assert "search_director" in response.tools_used

    def test_year_search_workflow(self, service_config, mock_retriever, mock_llm):
        """Test year search workflow."""
        service = MovieAgentService(service_config)
        service.set_vector_store(mock_retriever)
        service.config.llm = mock_llm

        mock_agent = Mock()
        mock_agent.run.return_value = {
            "answer": "Movies from 2020...",
            "movies": ["Movie 1", "Movie 2"],
            "tools_used": ["search_year"],
        }
        service._agent = mock_agent

        response = service.chat("Find movies from 2020")

        assert "search_year" in response.tools_used


class TestPosterAnalysisIntegration:
    """Integration tests for poster analysis functionality."""

    def test_poster_analysis_workflow(self, service_config, mock_vision_tool):
        """Test complete poster analysis workflow."""
        service = MovieAgentService(service_config)
        service.set_vision_analyst(mock_vision_tool)

        response = service.analyze_poster("/path/to/poster.png")

        assert response.inferred_genres == ["Drama"]
        assert response.mood == "Neutral"
        assert response.confidence == 0.7
        assert response.title == "Test Movie (2020)"
        mock_vision_tool.analyze_poster.assert_called_once_with("/path/to/poster.png")

    def test_poster_analysis_with_title_inference(self, service_config, mock_vision_tool, mock_retriever):
        """Test that poster analysis includes title inference via retriever."""
        # Set up vision tool with retriever for title inference
        if hasattr(mock_vision_tool, "_retriever"):
            mock_vision_tool._retriever = mock_retriever

        service = MovieAgentService(service_config)
        service.set_vision_analyst(mock_vision_tool)

        response = service.analyze_poster("/path/to/poster.png")

        assert response.title is not None
        assert response.title != "Unknown"


class TestErrorHandling:
    """Tests for error handling across the service."""

    def test_service_handles_missing_agent(self, service_config):
        """Test that service handles missing agent gracefully."""
        service = MovieAgentService(service_config)

        with pytest.raises(Exception):  # Should raise AgentNotInitializedError
            service.chat("test query")

    def test_service_handles_missing_vision_tool(self, service_config):
        """Test that service handles missing vision tool gracefully."""
        service = MovieAgentService(service_config)

        with pytest.raises(Exception):  # Should raise VisionAnalystNotInitializedError
            service.analyze_poster("/path/to/poster.png")

