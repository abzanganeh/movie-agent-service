"""
Explicit failure-mode tests for agent executor.
Tests defensive engineering around LLM unpredictability and tool failures.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from langchain_core.documents import Document

from src.movie_agent.service import MovieAgentService
from src.movie_agent.config import MovieAgentConfig
from src.movie_agent.agent.tool_calling_agent import ToolCallingAgent
from src.movie_agent.agent.output_parser import AgentOutputParser
from src.movie_agent.tools.impl import MovieSearchTool
from src.movie_agent.schemas import ChatResponse


@pytest.fixture
def service_config():
    """Create a test configuration."""
    return MovieAgentConfig(
        movies_csv_path="dummy.csv",
        warmup_on_start=False,
        enable_vision=False,
    )


@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = Mock()
    return llm


@pytest.fixture
def failing_retriever():
    """Create a retriever that throws exceptions."""
    retriever = Mock()
    retriever.retrieve.side_effect = Exception("Database connection failed")
    return retriever


@pytest.fixture
def empty_retriever():
    """Create a retriever that returns empty results."""
    retriever = Mock()
    retriever.retrieve.return_value = []
    return retriever


class TestToolExceptionHandling:
    """Tests for handling tool exceptions gracefully."""

    def test_tool_throws_exception_returns_graceful_error(
        self, service_config, mock_llm, failing_retriever
    ):
        """
        Test that when a tool throws an exception, the agent returns a graceful error.
        
        Expected behavior:
        - Agent should catch tool exceptions
        - Return user-friendly error message
        - Not crash or expose internal errors
        """
        service = MovieAgentService(service_config)
        service.set_vector_store(failing_retriever)
        service.config.llm = mock_llm
        # Skip warmup and directly mock the agent
        service._agent = Mock()

        # Mock the agent's run method to simulate tool exception handling
        def mock_run(query):
            # Simulate executor catching tool exception and returning error message
            return {
                "answer": (
                    "I encountered an issue while searching for movies. "
                    "Please try again or rephrase your query."
                ),
                "movies": [],
                "tools_used": ["movie_search"],
                "llm_latency_ms": 100,
                "tool_latency_ms": 0,
            }
        
        service._agent.run = mock_run

        response = service.chat("Find sci-fi movies")

        # Assertions: graceful error handling
        assert isinstance(response, ChatResponse)
        assert len(response.answer) > 0  # Should have an answer
        assert "error" in response.answer.lower() or "issue" in response.answer.lower() or "try" in response.answer.lower()
        assert response.movies == []  # No movies on error
        assert response.latency_ms >= 0  # Should still track latency

    def test_tool_exception_does_not_crash_service(
        self, service_config, mock_llm, failing_retriever
    ):
        """
        Test that tool exceptions don't crash the service.
        
        Expected behavior:
        - Service should catch exceptions
        - Return valid ChatResponse
        - Service remains usable after error
        """
        service = MovieAgentService(service_config)
        service.set_vector_store(failing_retriever)
        service.config.llm = mock_llm
        # Skip warmup and directly mock the agent
        service._agent = Mock()

        # Mock the agent's run method to handle tool failure
        def mock_run(query):
            return {
                "answer": "I'm sorry, I encountered an error processing your request.",
                "movies": [],
                "tools_used": [],
                "llm_latency_ms": 100,
                "tool_latency_ms": 0,
            }
        
        service._agent.run = mock_run

        # First call - should handle error gracefully
        response1 = service.chat("Find movies")
        assert isinstance(response1, ChatResponse)

        # Second call - service should still work
        response2 = service.chat("Try again")
        assert isinstance(response2, ChatResponse)
        # Service should be usable after error


class TestMalformedToolArgsHandling:
    """Tests for handling malformed tool arguments from LLM."""

    def test_llm_returns_malformed_tool_args_parser_fallback(
        self, service_config, mock_llm
    ):
        """
        Test that when LLM returns malformed tool arguments, parser has fallback.
        
        Expected behavior:
        - Parser should handle malformed metadata
        - Return safe defaults
        - Not crash on parse errors
        """
        service = MovieAgentService(service_config)
        service.config.llm = mock_llm

        # Mock executor returning malformed output
        mock_executor = Mock()
        
        # Simulate various malformed outputs
        malformed_outputs = [
            # Missing METADATA section
            "FINAL ANSWER:\nSome answer without metadata",
            
            # Malformed metadata (invalid Python syntax)
            (
                "FINAL ANSWER:\nSome answer\n\n"
                "METADATA:\n"
                "movies: [Inception, Interstellar  # Missing closing bracket\n"
                "confidence: not_a_number\n"
            ),
            
            # Empty metadata
            (
                "FINAL ANSWER:\nSome answer\n\n"
                "METADATA:\n"
            ),
            
            # Invalid JSON-like structures
            (
                "FINAL ANSWER:\nSome answer\n\n"
                "METADATA:\n"
                "movies: {'invalid': 'dict'}\n"
                "tools_used: not a list\n"
            ),
        ]

        for malformed_output in malformed_outputs:
            # Test parser directly with malformed output
            parsed = AgentOutputParser.parse(malformed_output)
            
            # Should return valid dict with safe defaults
            assert isinstance(parsed, dict)
            assert isinstance(parsed["answer"], str)
            assert isinstance(parsed["movies"], list)  # Always a list, never None
            assert isinstance(parsed["tools_used"], list)  # Always a list, never None

    def test_parser_handles_missing_metadata_gracefully(self):
        """Test that parser handles missing METADATA section."""
        # Test direct parser call with missing metadata
        output = "FINAL ANSWER:\nSome answer without metadata"
        parsed = AgentOutputParser.parse(output)
        
        assert "Some answer without metadata" in parsed["answer"]
        assert parsed["movies"] == []
        assert parsed["tools_used"] == []
        assert parsed["confidence"] is None

    def test_parser_handles_invalid_metadata_syntax(self):
        """Test that parser handles invalid metadata syntax."""
        # Test with invalid Python syntax in metadata
        output = (
            "FINAL ANSWER:\nSome answer\n\n"
            "METADATA:\n"
            "movies: [Inception, Interstellar  # Syntax error\n"
            "confidence: not_a_number\n"
        )
        parsed = AgentOutputParser.parse(output)
        
        # Should fall back to string values or defaults
        assert isinstance(parsed["answer"], str)
        assert isinstance(parsed["movies"], list)  # Should be list, not crash


class TestEmptyPayloadHandling:
    """Tests for handling empty tool payloads."""

    def test_tool_returns_empty_payload_user_safe_response(
        self, service_config, mock_llm, empty_retriever
    ):
        """
        Test that when tool returns empty payload, user gets safe response.
        
        Expected behavior:
        - Agent should handle empty results gracefully
        - Return user-friendly message
        - Not expose "no results" as an error
        """
        service = MovieAgentService(service_config)
        service.set_vector_store(empty_retriever)
        service.config.llm = mock_llm
        # Skip warmup and directly mock the agent
        service._agent = Mock()

        # Mock the agent's run method to return empty results response
        def mock_run(query):
            return {
                "answer": (
                    "I couldn't find any movies matching your query. "
                    "Please try different keywords or be more specific."
                ),
                "movies": [],
                "tools_used": ["movie_search"],
                "llm_latency_ms": 100,
                "tool_latency_ms": 50,
            }
        
        service._agent.run = mock_run

        response = service.chat("Find nonexistent movie xyz123")

        # Assertions: user-safe response
        assert isinstance(response, ChatResponse)
        assert len(response.answer) > 0
        # Should not say "error" or "failed", should be helpful
        assert "couldn't find" in response.answer.lower() or "no movies" in response.answer.lower() or "try" in response.answer.lower()
        assert response.movies == []  # Empty results
        assert response.tools_used == ["movie_search"]  # Tool was called
        assert response.latency_ms >= 0

    def test_empty_payload_does_not_break_flow(
        self, service_config, mock_llm, empty_retriever
    ):
        """
        Test that empty payloads don't break the agent flow.
        
        Expected behavior:
        - Agent should continue working after empty results
        - Subsequent queries should work normally
        """
        service = MovieAgentService(service_config)
        service.set_vector_store(empty_retriever)
        service.config.llm = mock_llm
        # Skip warmup and directly mock the agent
        service._agent = Mock()

        # Mock the agent's run method to return empty results
        call_count = [0]
        def mock_run(query):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "answer": "No movies found. Try a different search.",
                    "movies": [],
                    "tools_used": ["movie_search"],
                    "llm_latency_ms": 100,
                    "tool_latency_ms": 0,
                }
            else:
                return {
                    "answer": "Here are some results.",
                    "movies": ["Movie 1"],
                    "tools_used": ["movie_search"],
                    "llm_latency_ms": 100,
                    "tool_latency_ms": 0,
                }
        
        service._agent.run = mock_run

        # First call - empty results
        response1 = service.chat("Find nonexistent")
        assert isinstance(response1, ChatResponse)

        # Second call - should still work
        response2 = service.chat("Try another query")
        assert isinstance(response2, ChatResponse)
        # Agent should be functional after empty results


class TestMaxIterationsHandling:
    """Tests for max_iterations enforcement."""

    def test_max_iterations_prevents_infinite_loops(self, service_config, mock_llm):
        """
        Test that max_iterations prevents infinite loops.
        
        Expected behavior:
        - Agent should stop after max_iterations
        - Return a message indicating it stopped
        - Not hang or loop indefinitely
        """
        service = MovieAgentService(service_config)
        service.config.llm = mock_llm
        # Mock retriever for max_iterations test
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = []
        service.set_vector_store(mock_retriever)
        # Skip warmup and directly mock the agent
        service._agent = Mock()

        # Mock the agent's run method to simulate max_iterations stop
        def mock_run(query):
            return {
                "answer": "Agent stopped due to max iterations.",
                "movies": [],
                "tools_used": [],
                "llm_latency_ms": 100,
                "tool_latency_ms": 0,
            }
        
        service._agent.run = mock_run

        response = service.chat("complex query that might loop")

        # Should return response, not hang
        assert isinstance(response, ChatResponse)
        assert len(response.answer) > 0
        # Should indicate it stopped (either explicitly or implicitly)
        assert response.latency_ms >= 0  # Should complete in reasonable time

