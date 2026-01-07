"""
Tool output formatter for converting tool JSON responses to human-readable text.

OOP: Single Responsibility - handles only output formatting.
OOP: Separation of Concerns - formatting logic separated from agent execution.
OOP: Open/Closed - easy to extend with new formatters without modifying agent.
"""
import json
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ToolOutputFormatter(ABC):
    """Abstract base class for tool output formatters."""
    
    @abstractmethod
    def can_format(self, tool_name: str, tool_output: str) -> bool:
        """Check if this formatter can handle the given tool output."""
        pass
    
    @abstractmethod
    def format(self, tool_output: str) -> str:
        """Format tool output to human-readable text."""
        pass


class StatisticsFormatter(ToolOutputFormatter):
    """Formatter for get_movie_statistics tool output."""
    
    def can_format(self, tool_name: str, tool_output: str) -> bool:
        """Check if this is a statistics tool output."""
        return tool_name == 'get_movie_statistics'
    
    def format(self, tool_output: str) -> str:
        """Format statistics JSON to human-readable text."""
        try:
            stats_result = json.loads(tool_output)
            
            # Error handling
            if "error" in stats_result:
                return f"❌ {stats_result['error']}"
            
            # Highest rated movies
            if "highest_rating" in stats_result:
                movies = stats_result.get("movies", [])
                rating = stats_result.get("highest_rating", 0)
                if movies:
                    movie_list = "\n".join([
                        f"• {m.get('title', 'Unknown')} ({m.get('year', '?')}) - Rating: {m.get('rating', 0):.1f}/10"
                        for m in movies
                    ])
                    return f"🏆 Highest Rated Movies:\n\n{movie_list}\n\nRating: {rating:.1f}/10"
                else:
                    return f"Highest rating: {rating:.1f}/10"
            
            # Lowest rated movies
            if "lowest_rating" in stats_result:
                movies = stats_result.get("movies", [])
                rating = stats_result.get("lowest_rating", 0)
                if movies:
                    movie_list = "\n".join([
                        f"• {m.get('title', 'Unknown')} ({m.get('year', '?')}) - Rating: {m.get('rating', 0):.1f}/10"
                        for m in movies
                    ])
                    return f"📉 Lowest Rated Movies:\n\n{movie_list}\n\nRating: {rating:.1f}/10"
                else:
                    return f"Lowest rating: {rating:.1f}/10"
            
            # Top rated movies (list)
            if "top_rated" in stats_result:
                movies = stats_result.get("top_rated", [])
                count = stats_result.get("count", 0)
                if movies:
                    movie_list = "\n".join([
                        f"{i+1}. {m.get('title', 'Unknown')} ({m.get('year', '?')}) - Rating: {m.get('rating', 0):.1f}/10"
                        for i, m in enumerate(movies)
                    ])
                    return f"⭐ Top {count} Highest Rated Movies:\n\n{movie_list}"
                else:
                    return "No movies found with ratings."
            
            # Average rating
            if "average_rating" in stats_result:
                avg = stats_result.get("average_rating", 0)
                count = stats_result.get("count", 0)
                return f"📊 Average Rating: {avg:.2f}/10 (based on {count} movies)"
            
            # Count
            if "count" in stats_result:
                count = stats_result.get("count", 0)
                return f"📊 Total movies: {count}"
            
            # Genre distribution
            if "genre_distribution" in stats_result:
                dist = stats_result.get("genre_distribution", {})
                genre_list = "\n".join([
                    f"• {genre}: {count}"
                    for genre, count in sorted(dist.items(), key=lambda x: x[1], reverse=True)
                ])
                return f"📊 Genre Distribution:\n\n{genre_list}"
            
            # Fallback to raw JSON
            return tool_output
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to format statistics output: {e}")
            return tool_output


class ComparisonFormatter(ToolOutputFormatter):
    """Formatter for compare_movies tool output."""
    
    def can_format(self, tool_name: str, tool_output: str) -> bool:
        """Check if this is a comparison tool output."""
        return tool_name == 'compare_movies'
    
    def format(self, tool_output: str) -> str:
        """Format comparison JSON to human-readable text."""
        try:
            compare_result = json.loads(tool_output)
            movie_a = compare_result.get("movie_a", {})
            movie_b = compare_result.get("movie_b", {})
            
            # Build comparison lines
            lines = [
                f"🎬 Movie Comparison:\n",
                f"\n📽️ {movie_a.get('title', 'Unknown')} ({movie_a.get('year', '?')})",
                f"   Director: {movie_a.get('director', 'Unknown')}",
                f"   Genres: {', '.join(movie_a.get('genres', [])) if movie_a.get('genres') else 'Unknown'}",
            ]
            
            # Add rating if available
            if movie_a.get('rating'):
                lines.append(f"   Rating: {movie_a.get('rating', 'N/A')}/10")
            else:
                lines.append("   Rating: N/A")
            
            lines.extend([
                f"\n📽️ {movie_b.get('title', 'Unknown')} ({movie_b.get('year', '?')})",
                f"   Director: {movie_b.get('director', 'Unknown')}",
                f"   Genres: {', '.join(movie_b.get('genres', [])) if movie_b.get('genres') else 'Unknown'}",
            ])
            
            # Add rating if available
            if movie_b.get('rating'):
                lines.append(f"   Rating: {movie_b.get('rating', 'N/A')}/10")
            else:
                lines.append("   Rating: N/A")
            
            # Add rating comparison if both ratings available
            if movie_a.get('rating') and movie_b.get('rating'):
                rating_a = movie_a.get('rating', 0)
                rating_b = movie_b.get('rating', 0)
                if rating_a > rating_b:
                    lines.append(f"\n⭐ {movie_a.get('title')} has a higher rating ({rating_a:.1f} vs {rating_b:.1f})")
                elif rating_b > rating_a:
                    lines.append(f"\n⭐ {movie_b.get('title')} has a higher rating ({rating_b:.1f} vs {rating_a:.1f})")
                else:
                    lines.append(f"\n⭐ Both movies have the same rating ({rating_a:.1f})")
            
            return "\n".join(lines)
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to format comparison output: {e}")
            return tool_output


class QuizAnswerFormatter(ToolOutputFormatter):
    """Formatter for check_quiz_answer tool output."""
    
    def can_format(self, tool_name: str, tool_output: str) -> bool:
        """Check if this is a quiz answer tool output."""
        return tool_name == 'check_quiz_answer'
    
    def format(self, tool_output: str) -> str:
        """Format quiz answer JSON to human-readable feedback."""
        try:
            check_result = json.loads(tool_output)
            is_correct = check_result.get("is_correct", False)
            correct_answer = check_result.get("correct_answer", "")
            
            if is_correct:
                return f"✅ Correct! Great job! The answer was {correct_answer}."
            else:
                return f"❌ Incorrect. The correct answer was {correct_answer}. Let's try the next one!"
                
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to format quiz answer output: {e}")
            return tool_output


class ToolOutputFormatterFactory:
    """
    Factory for creating appropriate formatters.
    
    OOP: Factory Pattern - encapsulates formatter creation logic.
    OOP: Dependency Inversion - depends on abstractions (ToolOutputFormatter), not concrete classes.
    """
    
    _formatters: list[ToolOutputFormatter] = [
        StatisticsFormatter(),
        ComparisonFormatter(),
        QuizAnswerFormatter(),
    ]
    
    @classmethod
    def get_formatter(cls, tool_name: str, tool_output: str) -> Optional[ToolOutputFormatter]:
        """
        Get appropriate formatter for tool output.
        
        :param tool_name: Name of the tool
        :param tool_output: Raw tool output string
        :return: Formatter instance or None if no formatter matches
        """
        for formatter in cls._formatters:
            if formatter.can_format(tool_name, tool_output):
                return formatter
        return None
    
    @classmethod
    def format_output(cls, tool_name: str, tool_output: str) -> str:
        """
        Format tool output using appropriate formatter.
        
        :param tool_name: Name of the tool
        :param tool_output: Raw tool output string
        :return: Formatted human-readable string
        """
        formatter = cls.get_formatter(tool_name, tool_output)
        if formatter:
            return formatter.format(tool_output)
        return tool_output  # Return original if no formatter matches

