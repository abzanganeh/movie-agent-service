"""
Query relevance detector - determines if a user query is related to poster context.

OOP: Single Responsibility - solely responsible for detecting query relevance.
OOP: Separation of Concerns - query analysis logic separated from orchestration.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class QueryRelevanceDetector:
    """
    Detects if a user query is related to the current poster context.
    
    OOP: Single Responsibility - only decides relevance, does not act on it.
    """
    
    @staticmethod
    def is_query_related_to_poster(user_message: str, poster_title: Optional[str] = None) -> bool:
        """
        Determine if a query is related to the poster context.
        
        A query is considered related if:
        1. It explicitly mentions the poster title
        2. It asks for similar/recommended movies (after poster upload)
        3. It asks about the poster movie specifically
        
        A query is NOT related if:
        1. It asks about specific years/decades without mentioning the poster
        2. It asks for general statistics without poster context
        3. It asks about other movies by name
        4. It's a general search query with no poster reference
        
        :param user_message: User's query message
        :param poster_title: Title of the movie from poster (if available)
        :return: True if query is related to poster, False otherwise
        """
        user_msg_lower = user_message.lower().strip()
        
        # If no poster title, queries are not related
        if not poster_title:
            return False
        
        poster_title_lower = poster_title.lower().strip()
        
        # Explicit mentions of poster title
        if poster_title_lower in user_msg_lower:
            logger.debug(f"Query related: explicitly mentions poster title '{poster_title}'")
            return True
        
        # Similarity/recommendation queries (after poster upload)
        similarity_phrases = [
            "like this",
            "similar to",
            "more like",
            "similar movies",
            "recommend movies",
            "movies like it",
            "movies like this",
        ]
        if any(phrase in user_msg_lower for phrase in similarity_phrases):
            logger.debug(f"Query related: similarity/recommendation query")
            return True
        
        # Questions about the poster movie
        question_patterns = [
            r"what.*movie",
            r"which.*movie",
            r"tell me about",
            r"what is.*about",
        ]
        for pattern in question_patterns:
            if re.search(pattern, user_msg_lower):
                # If it's a general question without specific movie name, it might be about the poster
                # But if it mentions another movie name, it's not about the poster
                if poster_title_lower in user_msg_lower:
                    logger.debug(f"Query related: question about poster movie")
                    return True
        
        # Unrelated patterns (year/decade queries, general statistics, specific other movies)
        unrelated_patterns = [
            r"\b(19|20)\d{2}s?\b",  # Years like "2010", "2010s", "1990s"
            r"\bfrom\s+\d{4}\b",  # "from 2010"
            r"\bin\s+\d{4}\b",  # "in 1990"
            r"\b\d{4}s\b",  # Decades like "90s", "2000s"
            r"best.*movies",  # "best movies from 2010"
            r"top.*movies",  # "top movies"
            r"statistics",  # General statistics
            r"compare",  # Comparisons (unless comparing to poster movie)
        ]
        
        # Check if query matches unrelated patterns AND doesn't mention poster
        for pattern in unrelated_patterns:
            if re.search(pattern, user_msg_lower):
                # If it mentions the poster title, it's still related
                if poster_title_lower not in user_msg_lower:
                    logger.debug(f"Query unrelated: matches pattern '{pattern}' without poster mention")
                    return False
        
        # If query mentions another specific movie (not the poster), it's unrelated
        # Extract potential movie titles (capitalized words, 2+ words)
        # This is a heuristic - might have false positives, but better than false negatives
        movie_title_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        mentioned_titles = re.findall(movie_title_pattern, user_message)
        for title in mentioned_titles:
            title_lower = title.lower()
            # If it's not the poster title and looks like a movie title, it's unrelated
            if title_lower != poster_title_lower and len(title.split()) >= 2:
                logger.debug(f"Query unrelated: mentions other movie '{title}'")
                return False
        
        # Default: if we can't determine, assume unrelated to avoid polluting queries
        # This is conservative - better to miss context than add wrong context
        logger.debug(f"Query unrelated: default (no clear relation to poster)")
        return False

