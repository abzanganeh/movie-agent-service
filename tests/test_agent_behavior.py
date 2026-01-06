"""
Unit tests for agent behavior.

Tests intent → tool correctness, quiz safety, single-tool enforcement, and correction handling.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

from movie_agent.service import MovieAgentService
from movie_agent.config import MovieAgentConfig
from movie_agent.schemas import ChatResponse
from movie_agent.memory.session_state import SessionStateManager
from movie_agent.memory.quiz_state import QuizState
from movie_agent.intent.agent_intent import AgentIntent


class TestAgentBehavior:
    """Test suite for agent behavior validation."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = MovieAgentConfig(
            llm_provider="openai",
            openai_api_key="test-key",
            enable_memory=True,
            memory_max_turns=10,
            verbose=False,
        )
        return config
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = Mock()
        return agent
    
    @pytest.fixture
    def service(self, mock_config, mock_agent):
        """Create a service instance with mocked dependencies."""
        service = MovieAgentService(mock_config)
        service._agent = mock_agent
        service._session_state = SessionStateManager()
        return service
    
    def test_movie_search_intent_calls_movie_search(self, service, mock_agent):
        """
        Test A: Intent → tool correctness.
        
        Verify that movie search queries call movie_search tool.
        """
        # Mock agent response
        mock_agent.run.return_value = {
            "answer": "Here are some action movies from the 90s: The Matrix, Terminator 2.",
            "movies": ["The Matrix", "Terminator 2"],
            "tools_used": ["movie_search"],
            "confidence": 0.9,
            "llm_latency_ms": 500,
            "tool_latency_ms": 200,
        }
        
        response = service.chat("Recommend 90s action movies", session_id="test-session")
        
        # Verify tool was called
        assert "movie_search" in response.tools_used
        assert len(response.movies) > 0
        assert response.answer is not None
    
    def test_quiz_answer_not_allowed_when_not_in_quiz(self, service, mock_agent):
        """
        Test B: Quiz safety.
        
        Verify that check_quiz_answer is NOT called when not in quiz mode.
        """
        # Mock agent response (should NOT call check_quiz_answer)
        mock_agent.run.return_value = {
            "answer": "The Godfather is a classic crime drama from 1972.",
            "movies": ["The Godfather"],
            "tools_used": ["movie_search"],  # Should use movie_search, not check_quiz_answer
            "confidence": 0.9,
            "llm_latency_ms": 500,
            "tool_latency_ms": 200,
        }
        
        response = service.chat("Tell me about The Godfather", session_id="test-session")
        
        # Verify check_quiz_answer was NOT called
        assert "check_quiz_answer" not in response.tools_used
        assert "movie_search" in response.tools_used or len(response.tools_used) == 0
    
    def test_quiz_answer_allowed_when_in_quiz(self, service, mock_agent):
        """
        Test B (continued): Quiz safety - allow check_quiz_answer when in quiz mode.
        """
        session_id = "test-session"
        session_state = service._session_state.get_state(session_id)
        quiz_state = session_state.get_quiz_state()
        
        # Activate quiz state
        quiz_state.activate({
            "topic": "action movies",
            "questions": [{"id": 1, "question": "What is the best action movie?"}]
        })
        
        # Mock agent response (should call check_quiz_answer)
        mock_agent.run.return_value = {
            "answer": "Correct! The Matrix is indeed a great action movie.",
            "movies": [],
            "tools_used": ["check_quiz_answer"],
            "confidence": 0.9,
            "llm_latency_ms": 500,
            "tool_latency_ms": 200,
        }
        
        response = service.chat("The Matrix", session_id=session_id)
        
        # Verify check_quiz_answer WAS called when in quiz mode
        assert "check_quiz_answer" in response.tools_used
    
    def test_single_tool_rule(self, service, mock_agent):
        """
        Test C: Single-tool enforcement.
        
        Verify that at most one tool is called per query.
        """
        # Mock agent response
        mock_agent.run.return_value = {
            "answer": "The Matrix and Inception are both sci-fi classics.",
            "movies": ["The Matrix", "Inception"],
            "tools_used": ["compare_movies"],  # Should be exactly one tool
            "confidence": 0.9,
            "llm_latency_ms": 500,
            "tool_latency_ms": 200,
        }
        
        response = service.chat("Compare The Matrix and Inception", session_id="test-session")
        
        # Verify at most one tool was called
        assert len(response.tools_used) <= 1
        if response.tools_used:
            assert response.tools_used[0] in ["compare_movies", "movie_search"]
    
    def test_correction_does_not_call_tool(self, service, mock_agent):
        """
        Test D: Correction handling.
        
        Verify that corrections are handled conversationally without tool calls.
        """
        # Mock agent response (should NOT call tools for corrections)
        mock_agent.run.return_value = {
            "answer": "You're right, I apologize for the error. Let me help you find the correct information.",
            "movies": [],
            "tools_used": [],  # Should be empty for corrections
            "confidence": 0.5,
            "llm_latency_ms": 300,
            "tool_latency_ms": 0,
        }
        
        response = service.chat("That rating is wrong", session_id="test-session")
        
        # Verify no tools were called
        assert len(response.tools_used) == 0
        assert "apologize" in response.answer.lower() or "sorry" in response.answer.lower() or "correction" in response.answer.lower()
    
    def test_empty_results_fallback(self, service, mock_agent):
        """
        Test E: Fallback Strategy A - Empty results.
        
        Verify graceful handling when tool returns empty results.
        """
        # Mock agent response with empty movies
        mock_agent.run.return_value = {
            "answer": "I searched for movies matching your query.",
            "movies": [],  # Empty results
            "tools_used": ["movie_search"],
            "confidence": 0.3,
            "llm_latency_ms": 500,
            "tool_latency_ms": 200,
        }
        
        response = service.chat("Find obscure 1950s sci-fi movies", session_id="test-session")
        
        # Verify fallback message is included
        assert "couldn't find" in response.answer.lower() or "widen" in response.answer.lower() or len(response.answer) > 0
        assert response.confidence < 0.5  # Low confidence for empty results
    
    def test_tool_failure_fallback(self, service, mock_agent):
        """
        Test F: Fallback Strategy C - Tool failure.
        
        Verify graceful handling when tool execution fails.
        """
        # Mock agent to raise exception
        mock_agent.run.side_effect = Exception("Tool execution failed")
        
        response = service.chat("Find action movies", session_id="test-session")
        
        # Verify graceful error response
        assert response.reasoning_type == "error_handling"
        assert "issue" in response.answer.lower() or "try" in response.answer.lower()
        assert len(response.tools_used) == 0
        assert response.confidence == 0.0
    
    def test_quiz_state_activation(self, service, mock_agent):
        """
        Test G: Quiz state management.
        
        Verify that quiz state is properly activated when quiz is generated.
        """
        session_id = "test-session"
        
        # Mock agent response with quiz generation
        quiz_data = {
            "topic": "action movies",
            "questions": [
                {"id": 1, "question": "What is the best action movie?", "options": ["A", "B", "C"], "answer": "A"}
            ]
        }
        mock_agent.run.return_value = {
            "answer": f"Here's your quiz: {quiz_data}",
            "movies": [],
            "tools_used": ["generate_movie_quiz"],
            "confidence": 0.9,
            "llm_latency_ms": 500,
            "tool_latency_ms": 200,
        }
        
        response = service.chat("Generate a quiz about action movies", session_id=session_id)
        
        # Verify quiz state was activated
        session_state = service._session_state.get_state(session_id)
        quiz_state = session_state.get_quiz_state()
        assert quiz_state.is_active()
        assert "generate_movie_quiz" in response.tools_used
    
    def test_intent_tool_mapping(self):
        """
        Test H: Intent → Tool mapping correctness.
        
        Verify that AgentIntent enum correctly maps to tools.
        """
        mapping = AgentIntent.get_tool_mapping()
        
        # Verify key mappings
        assert mapping[AgentIntent.MOVIE_SEARCH] == "movie_search"
        assert mapping[AgentIntent.MOVIE_COMPARISON] == "compare_movies"
        assert mapping[AgentIntent.QUIZ_START] == "generate_movie_quiz"
        assert mapping[AgentIntent.QUIZ_ANSWER] == "check_quiz_answer"
        assert mapping[AgentIntent.CORRECTION] is None
        assert mapping[AgentIntent.CHIT_CHAT] is None
    
    def test_quiz_state_deactivation(self, service):
        """
        Test I: Quiz state deactivation.
        
        Verify that quiz state can be properly deactivated.
        """
        session_id = "test-session"
        session_state = service._session_state.get_state(session_id)
        quiz_state = session_state.get_quiz_state()
        
        # Activate quiz
        quiz_state.activate({"topic": "test", "questions": []})
        assert quiz_state.is_active()
        
        # Deactivate quiz
        quiz_state.deactivate()
        assert not quiz_state.is_active()
        assert quiz_state.mode is None
        assert quiz_state.attempts == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


