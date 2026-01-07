"""
Similarity Query Analyzer - Decides which movies to exclude from similarity searches.

OOP: Single Responsibility - analyzes queries to determine exclusion criteria.
Follows design rule: This class DECIDES, but does NOT ACT.
"""
import re
import logging

logger = logging.getLogger(__name__)


class SimilarityQueryAnalyzer:
    """
    Analyzes similarity search queries to determine exclusion criteria.
    
    OOP: Single Responsibility - decision logic only.
    This class DECIDES which title to exclude, but does NOT filter results.
    """
    
    @staticmethod
    def extract_exclude_title(query: str) -> str | None:
        """
        Extract movie title to exclude from similarity search results.
        
        OOP: Single Responsibility - decision logic (what to exclude).
        Does NOT filter - only decides.
        
        :param query: Search query string
        :return: Movie title to exclude, or None if no exclusion needed
        """
        query_lower = query.lower()
        exclude_title = None
        
        # Priority 1: Extract title from end of query (most reliable for complete titles)
        # Pattern: "like [title]" at end of query
        # Example: "comedy family movies like Home Alone"
        end_pattern = r"like\s+(.+)$"
        match = re.search(end_pattern, query_lower, re.IGNORECASE)
        if match:
            exclude_title = match.group(1).strip()
            logger.debug(f"SimilarityQueryAnalyzer: Extracted title from end pattern: '{exclude_title}'")
            return exclude_title
        
        # Priority 2: Extract from "like [title]" anywhere in query
        like_patterns = [
            r"like\s+(.+?)(?:\s+movies|\s+movie|$)",
            r"similar to\s+(.+?)(?:\s+movies|\s+movie|$)",
            r"more like\s+(.+?)(?:\s+movies|\s+movie|$)",
        ]
        
        for pattern in like_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                exclude_title = match.group(1).strip()
                logger.debug(f"SimilarityQueryAnalyzer: Extracted title from pattern '{pattern}': '{exclude_title}'")
                return exclude_title
        
        return None

