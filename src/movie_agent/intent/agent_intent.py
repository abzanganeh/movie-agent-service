"""
Formal intent taxonomy for agent behavior.

Provides explicit, enforceable intent contracts for production-grade agent routing.
Includes deterministic intent detection function for production-safe, testable routing.
"""
from enum import Enum
import re
from typing import Optional


class AgentIntent(str, Enum):
    """
    Formal intent taxonomy for agent behavior.
    
    This enum provides explicit, testable intent contracts.
    Intent detection uses deterministic pattern matching (production-safe, testable).
    """
    MOVIE_SEARCH = "movie_search"
    MOVIE_COMPARISON = "movie_comparison"
    QUIZ_START = "quiz_start"
    QUIZ_ANSWER = "quiz_answer"
    QUIZ_NEXT = "quiz_next"
    ACTOR_LOOKUP = "actor_lookup"
    DIRECTOR_LOOKUP = "director_lookup"
    YEAR_LOOKUP = "year_lookup"
    POSTER_QUERY = "poster_query"
    CORRECTION = "correction"
    CHIT_CHAT = "chit_chat"
    
    @classmethod
    def get_tool_mapping(cls) -> dict:
        """
        Map intents to their corresponding tools.
        
        :return: Dictionary mapping intent to tool name
        """
        return {
            cls.MOVIE_SEARCH: "movie_search",
            cls.MOVIE_COMPARISON: "compare_movies",
            cls.QUIZ_START: "generate_movie_quiz",
            cls.QUIZ_ANSWER: "check_quiz_answer",
            cls.QUIZ_NEXT: None,  # No tool - handled in service layer
            cls.ACTOR_LOOKUP: "search_actor",
            cls.DIRECTOR_LOOKUP: "search_director",
            cls.YEAR_LOOKUP: "search_year",
            cls.POSTER_QUERY: "movie_search",  # Uses movie_search after vision
            cls.CORRECTION: None,  # No tool
            cls.CHIT_CHAT: None,  # No tool
        }
    
    @classmethod
    def requires_tool(cls, intent: "AgentIntent") -> bool:
        """
        Check if an intent requires a tool call.
        
        :param intent: AgentIntent enum value
        :return: True if intent requires a tool, False otherwise
        """
        return cls.get_tool_mapping().get(intent) is not None
    
    @classmethod
    def get_tool_for_intent(cls, intent: "AgentIntent") -> Optional[str]:
        """
        Get the tool name for a given intent.
        
        :param intent: AgentIntent enum value
        :return: Tool name or None if no tool required
        """
        return cls.get_tool_mapping().get(intent)


def detect_intent(user_input: str, quiz_active: bool = False) -> AgentIntent:
    """
    Detect user intent from input text using deterministic pattern matching.
    
    Production-safe, testable, and LLM-agnostic intent classification.
    Uses keyword/pattern matching for fast, reliable intent detection.
    
    :param user_input: User's input text
    :param quiz_active: Whether a quiz is currently active in the session
    :return: AgentIntent enum value
    """
    text = user_input.lower().strip()
    
    # Quiz-related intents (state-aware)
    if quiz_active:
        # Navigation phrases - advance to next question
        next_patterns = [
            r'\b(next|next one|next question|continue|skip|move on|proceed|go to next)\b',
            r'^(next|continue|skip)$',
        ]
        if any(re.search(pattern, text) for pattern in next_patterns):
            return AgentIntent.QUIZ_NEXT  # User wants next question
        
        # Exception: explicit quiz start request
        if re.search(r'\b(play|quiz|trivia|game|start game|new quiz|another quiz)\b', text):
            return AgentIntent.QUIZ_START  # User wants to start a new quiz
        return AgentIntent.QUIZ_ANSWER  # User is answering current quiz
    
    # Start quiz (only when not in quiz mode)
    # Match "play", "quiz", "trivia", "game", "let's play", "lets play", etc.
    quiz_patterns = [
        r'\b(play|quiz|trivia|game|shoot|start game)\b',
        r"let'?s\s+play",
        r"lets\s+play",
    ]
    if any(re.search(pattern, text) for pattern in quiz_patterns):
        return AgentIntent.QUIZ_START
    
    # Poster query
    if 'poster' in text or re.search(r'\.(jpg|png|jpeg|image)', text, re.IGNORECASE):
        return AgentIntent.POSTER_QUERY
    
    # Actor lookup
    if re.search(r'\b(actor|cast|who stars? in|starring|played by)\b', text):
        return AgentIntent.ACTOR_LOOKUP
    
    # Director lookup
    if re.search(r'\b(director|who directed|directed by|helmed by)\b', text):
        return AgentIntent.DIRECTOR_LOOKUP
    
    # Year lookup
    if re.search(r'\b(year|from|released in|movies? (from|in) (19|20)\d{2})\b', text):
        return AgentIntent.YEAR_LOOKUP
    
    # Correction/feedback
    if re.search(r'\b(wrong|incorrect|no|that\'?s not|not right|fix|correction|mistake|error|actually|belongs to|some of these)\b', text):
        return AgentIntent.CORRECTION
    
    # Movie comparison
    if re.search(r'\b(compare|vs|versus|better than|difference between|which is better|prefer)\b', text):
        return AgentIntent.MOVIE_COMPARISON
    
    # Movie search (fallback for movie-related queries)
    movie_keywords = ['movie', 'movies', 'film', 'films', 'show', 'recommend', 'find', 'search', 'suggest', 'watch']
    if any(keyword in text for keyword in movie_keywords):
        return AgentIntent.MOVIE_SEARCH
    
    # Greetings and chit-chat
    greeting_keywords = ['hi', 'hello', 'hey', 'greetings', 'thanks', 'thank you', 'bye', 'goodbye']
    if any(keyword in text for keyword in greeting_keywords) or len(text.split()) <= 2:
        return AgentIntent.CHIT_CHAT
    
    # Default: assume movie search for longer queries
    if len(text.split()) > 2:
        return AgentIntent.MOVIE_SEARCH
    
    # Very short queries default to chit-chat
    return AgentIntent.CHIT_CHAT

