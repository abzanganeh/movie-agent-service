"""
Deterministic intent router for query classification.

Routes user queries to appropriate intents without LLM calls.
Fast, safe, and predictable.
"""
import re
from .intent_types import IntentType


class IntentRouter:
    """
    Deterministic intent router.
    
    Classifies user queries into intent types using simple pattern matching.
    No LLM, no fuzzy logic, no guessing - just fast, safe routing.
    """
    
    # Intent keyword sets
    GREETINGS = {"hi", "hello", "hey", "greetings"}
    GAME_KEYWORDS = {"play game", "quiz", "movie quiz", "trivia", "game"}
    COMPARE_KEYWORDS = {"compare", "vs", "versus", "better than", "difference between"}
    STATS_KEYWORDS = {"stats", "statistics", "average", "most", "count", "distribution"}
    MOVIE_KEYWORDS = {"movie", "movies", "film", "recommend", "find", "search", "show"}
    
    def route(self, query: str) -> IntentType:
        """
        Route a query to an intent type.
        
        :param query: User query string
        :return: IntentType enum value
        """
        q = query.lower().strip()
        
        # Empty query
        if not q:
            return IntentType.UNKNOWN
        
        # Exact greeting match
        if q in self.GREETINGS:
            return IntentType.GREETING
        
        # Game intent (must contain game keywords)
        if any(keyword in q for keyword in self.GAME_KEYWORDS):
            return IntentType.GAME
        
        # Compare intent
        if any(keyword in q for keyword in self.COMPARE_KEYWORDS):
            return IntentType.COMPARE_MOVIES
        
        # Statistics intent
        if any(keyword in q for keyword in self.STATS_KEYWORDS):
            return IntentType.STATISTICS
        
        # Poster analysis (image path or explicit poster mention)
        if "poster" in q or re.search(r"\.(jpg|png|jpeg)$", q, re.IGNORECASE):
            return IntentType.POSTER_ANALYSIS
        
        # Movie search (contains movie keywords or looks like a search query)
        if any(keyword in q for keyword in self.MOVIE_KEYWORDS):
            return IntentType.MOVIE_SEARCH
        
        # Check for meaningless queries (common patterns that don't map to intents)
        meaningless_patterns = {
            "let have fun", "have fun", "let's have fun", "lets have fun",
            "play", "fun", "go", "do", "what", "how", "why", "when", "where",
        }
        
        if q in meaningless_patterns:
            return IntentType.UNKNOWN
        
        # Very short queries (1-2 words) that aren't greetings are likely meaningless
        words = q.split()
        if len(words) <= 2 and q not in self.GREETINGS:
            # Check if it's a common meaningless phrase
            if q in meaningless_patterns or any(word in meaningless_patterns for word in words):
                return IntentType.UNKNOWN
        
        # Default: assume movie search for longer queries
        return IntentType.MOVIE_SEARCH

