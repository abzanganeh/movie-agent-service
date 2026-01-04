"""
Intent types for query classification.

Defines the possible intents a user query can have.
"""
from enum import Enum, auto


class IntentType(Enum):
    """Types of user intents."""
    GREETING = auto()
    MOVIE_SEARCH = auto()
    POSTER_ANALYSIS = auto()
    COMPARE_MOVIES = auto()
    GAME = auto()
    STATISTICS = auto()
    UNKNOWN = auto()

