"""
Comprehensive tests for all movie agent tools.
Based on Colab test patterns, adapted for pytest.
"""
import json
import pytest
from unittest.mock import Mock, MagicMock
from langchain_core.documents import Document

from src.movie_agent.tools.impl import MovieSearchTool, PosterAnalysisTool
from src.movie_agent.tools.quiz_tools import (
    GenerateMovieQuizTool,
    CheckQuizAnswerTool,
    CompareMoviesTool,
)
from src.movie_agent.tools.search_tools import (
    SearchActorTool,
    SearchDirectorTool,
    SearchYearTool,
)
from src.movie_agent.schemas import PosterAnalysisResponse


class TestMovieSearchTool:
    """Tests for movie_search tool."""

    def test_movie_search_returns_formatted_results(self):
        """Test that movie_search formats results correctly."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            Document(
                page_content="Sci-fi movie about dreams",
                metadata={"title": "Inception", "year": 2010}
            ),
            Document(
                page_content="Space exploration",
                metadata={"title": "Interstellar", "year": 2014}
            ),
        ]

        tool = MovieSearchTool(retriever=mock_retriever, top_k=5)
        result = tool._run("sci-fi movies")

        assert "Inception" in result
        assert "2010" in result
        assert "Interstellar" in result
        assert "2014" in result

    def test_movie_search_handles_empty_results(self):
        """Test that movie_search handles no results gracefully."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = []

        tool = MovieSearchTool(retriever=mock_retriever)
        result = tool._run("nonexistent movie")

        assert result == "No movies found matching the query."

    def test_movie_search_respects_top_k(self):
        """Test that movie_search respects top_k parameter."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            Document(page_content=f"Movie {i}", metadata={"title": f"Movie {i}", "year": 2000 + i})
            for i in range(10)
        ]

        tool = MovieSearchTool(retriever=mock_retriever, top_k=3)
        tool._run("test query")

        mock_retriever.retrieve.assert_called_once()
        call_args = mock_retriever.retrieve.call_args
        assert call_args[1]["k"] == 3


class TestGenerateMovieQuizTool:
    """Tests for generate_movie_quiz tool."""

    def test_generate_quiz_creates_valid_questions(self):
        """Test that quiz generation creates valid question structure."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            Document(
                page_content="Test movie",
                metadata={"title": "Test Movie", "year": 2020}
            ),
        ]

        tool = GenerateMovieQuizTool(retriever=mock_retriever, top_k=5)
        result = tool._run("sci-fi", num_questions=1)

        quiz_data = json.loads(result)
        assert "topic" in quiz_data
        assert "questions" in quiz_data
        assert len(quiz_data["questions"]) == 1
        assert quiz_data["questions"][0]["id"] == 1
        assert "question" in quiz_data["questions"][0]
        assert "options" in quiz_data["questions"][0]
        assert "answer" in quiz_data["questions"][0]
        assert quiz_data["questions"][0]["answer"] == "2020"

    def test_generate_quiz_handles_multiple_questions(self):
        """Test that quiz generation handles multiple questions."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            Document(
                page_content=f"Movie {i}",
                metadata={"title": f"Movie {i}", "year": 2020 + i}
            )
            for i in range(3)
        ]

        tool = GenerateMovieQuizTool(retriever=mock_retriever)
        result = tool._run("test", num_questions=3)

        quiz_data = json.loads(result)
        assert len(quiz_data["questions"]) == 3
        assert quiz_data["questions"][0]["id"] == 1
        assert quiz_data["questions"][1]["id"] == 2
        assert quiz_data["questions"][2]["id"] == 3

    def test_generate_quiz_handles_empty_results(self):
        """Test that quiz generation handles no results gracefully."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = []

        tool = GenerateMovieQuizTool(retriever=mock_retriever)
        result = tool._run("nonexistent", num_questions=3)

        quiz_data = json.loads(result)
        assert quiz_data["questions"] == []
        assert "note" in quiz_data


class TestCheckQuizAnswerTool:
    """Tests for check_quiz_answer tool."""

    def test_check_answer_correct(self):
        """Test that correct answers are identified."""
        tool = CheckQuizAnswerTool()
        result = tool._run(
            question="What year was Inception released?",
            user_answer="2010",
            correct_answer="2010"
        )

        data = json.loads(result)
        assert data["is_correct"] is True
        assert "Correct!" in data["feedback"]

    def test_check_answer_incorrect(self):
        """Test that incorrect answers are identified."""
        tool = CheckQuizAnswerTool()
        result = tool._run(
            question="What year was Inception released?",
            user_answer="2011",
            correct_answer="2010"
        )

        data = json.loads(result)
        assert data["is_correct"] is False
        assert "Incorrect" in data["feedback"]

    def test_check_answer_case_insensitive(self):
        """Test that answer checking is case-insensitive."""
        tool = CheckQuizAnswerTool()
        result = tool._run(
            question="Test question",
            user_answer="  ANSWER  ",
            correct_answer="answer"
        )

        data = json.loads(result)
        assert data["is_correct"] is True


class TestCompareMoviesTool:
    """Tests for compare_movies tool."""

    def test_compare_movies_returns_comparison(self):
        """Test that movie comparison returns structured comparison."""
        mock_retriever = Mock()
        mock_retriever.retrieve.side_effect = [
            [Document(
                page_content="Movie A",
                metadata={"title": "Movie A", "year": 2020, "genres": ["Action"], "director": "Director A"}
            )],
            [Document(
                page_content="Movie B",
                metadata={"title": "Movie B", "year": 2021, "genres": ["Drama"], "director": "Director B"}
            )],
        ]

        tool = CompareMoviesTool(retriever=mock_retriever)
        result = tool._run("Movie A", "Movie B")

        data = json.loads(result)
        assert "movie_a" in data
        assert "movie_b" in data
        assert "comparison" in data
        assert data["movie_a"]["title"] == "Movie A"
        assert data["movie_b"]["title"] == "Movie B"

    def test_compare_movies_handles_missing_movie(self):
        """Test that comparison handles missing movies gracefully."""
        mock_retriever = Mock()
        mock_retriever.retrieve.side_effect = [
            [Document(page_content="Movie A", metadata={"title": "Movie A"})],
            [],  # Movie B not found
        ]

        tool = CompareMoviesTool(retriever=mock_retriever)
        result = tool._run("Movie A", "Nonexistent")

        data = json.loads(result)
        assert data["movie_b"]["title"] == "Unknown"


class TestSearchActorTool:
    """Tests for search_actor tool."""

    def test_search_actor_returns_formatted_results(self):
        """Test that actor search returns formatted results."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            Document(
                page_content="Movie with actor",
                metadata={"title": "Movie 1", "year": 2020}
            ),
        ]

        tool = SearchActorTool(retriever=mock_retriever)
        result = tool._run("Tom Hanks")

        assert "Movie 1" in result
        assert "2020" in result
        mock_retriever.retrieve.assert_called_once()
        assert "actor: Tom Hanks" in mock_retriever.retrieve.call_args[0][0]


class TestSearchDirectorTool:
    """Tests for search_director tool."""

    def test_search_director_returns_formatted_results(self):
        """Test that director search returns formatted results."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            Document(
                page_content="Movie by director",
                metadata={"title": "Movie 1", "year": 2020}
            ),
        ]

        tool = SearchDirectorTool(retriever=mock_retriever)
        result = tool._run("Christopher Nolan")

        assert "Movie 1" in result
        mock_retriever.retrieve.assert_called_once()
        assert "director: Christopher Nolan" in mock_retriever.retrieve.call_args[0][0]


class TestSearchYearTool:
    """Tests for search_year tool."""

    def test_search_year_returns_formatted_results(self):
        """Test that year search returns formatted results."""
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            Document(
                page_content="Movie from year",
                metadata={"title": "Movie 1", "year": 2020}
            ),
        ]

        tool = SearchYearTool(retriever=mock_retriever)
        result = tool._run("2020")

        assert "Movie 1" in result
        mock_retriever.retrieve.assert_called_once()
        assert "year: 2020" in mock_retriever.retrieve.call_args[0][0]


class TestPosterAnalysisTool:
    """Tests for analyze_movie_poster tool."""

    def test_poster_analysis_returns_formatted_result(self):
        """Test that poster analysis returns formatted result with title."""
        mock_vision_tool = Mock()
        mock_vision_tool.analyze_poster.return_value = PosterAnalysisResponse(
            inferred_genres=["Drama", "Thriller"],
            mood="Dark",
            confidence=0.85,
            title="The Dark Knight (2008)"
        )

        tool = PosterAnalysisTool(vision_tool=mock_vision_tool)
        result = tool._run("/path/to/poster.png")

        assert "The Dark Knight" in result
        assert "Drama" in result
        assert "Thriller" in result
        assert "Dark" in result
        assert "0.85" in result

    def test_poster_analysis_handles_errors(self):
        """Test that poster analysis handles errors gracefully."""
        mock_vision_tool = Mock()
        mock_vision_tool.analyze_poster.side_effect = Exception("Image not found")

        tool = PosterAnalysisTool(vision_tool=mock_vision_tool)
        result = tool._run("/invalid/path.png")

        assert "Failed to analyze poster" in result
        assert "Image not found" in result

