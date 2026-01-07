from typing import List, Optional, Any
from pydantic import Field, BaseModel
from langchain.tools import BaseTool
from langchain_core.documents import Document
from .retriever_tool import RetrieverTool
from .vision_tool import VisionTool
from .similarity_analyzer import SimilarityQueryAnalyzer
from ..schemas import PosterAnalysisResponse


class MovieSearchArgs(BaseModel):
    query: str


class MovieSearchTool(BaseTool):
    """
    LangChain adapter for the RetrieverTool protocol.
    Exposes movie semantic search to the tool-calling agent.
    """

    name: str = "movie_search"
    description: str = (
        "Use this tool to find, search, or discover movies by description, genre, year, title, or attributes. "
        "Use for: 'find comedies', 'show me action movies', 'recommend sci-fi', 'movies from 90s', etc. "
        "IMPORTANT: When user asks for similar movies (e.g., 'find more movies like this'), prioritize GENRE/MOOD matching, "
        "not just title similarity. Use genre-based queries like 'comedy family movies' instead of just the movie title. "
        "Input should be a natural language query describing what movies to find."
    )
    # Pydantic v2 requires declared fields for assignment
    retriever: Any = Field(default=None)
    top_k: int = Field(default=5)

    def __init__(self, retriever, top_k: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.retriever = retriever
        self.top_k = int(top_k)
    
    args_schema: type[BaseModel] = MovieSearchArgs

    def _run(self, query: str) -> str:
        """
        Run movie search and filter results.
        
        OOP: Single Responsibility - executes search and filters results.
        
        If query contains "like [title]" pattern, excludes that title from results.
        """
        results: List[Document] = self.retriever.retrieve(query, k=self.top_k * 2)
        
        # Filter out original movie if query contains "like [title]" pattern
        # This handles similarity searches where user wants movies "like Home Alone"
        filtered_results = self._filter_similarity_results(results, query)
        
        # Limit to top_k after filtering
        filtered_results = filtered_results[:self.top_k]
        
        if not filtered_results:
            return "No movies found matching the query."
        
        summaries = [
            f"{doc.metadata.get('title', 'Unknown')} ({doc.metadata.get('year', 'N/A')})"
            for doc in filtered_results
        ]
        return "; ".join(summaries)
    
    def _filter_similarity_results(self, results: List[Document], query: str) -> List[Document]:
        """
        Filter out the original movie from similarity search results.
        
        OOP: Single Responsibility - ACTS only (filters results).
        Does NOT decide - uses SimilarityQueryAnalyzer to decide what to exclude.
        Follows design rule: Tool acts, analyzer decides.
        
        :param results: List of Document objects from search
        :param query: Search query string
        :return: Filtered list of documents
        """
        import logging
        import re
        
        logger = logging.getLogger(__name__)
        
        # OOP: Decision is made by SimilarityQueryAnalyzer (decides), not by this Tool (acts)
        exclude_title = SimilarityQueryAnalyzer.extract_exclude_title(query)
        
        # Filter out the excluded title (case-insensitive comparison)
        if exclude_title:
            exclude_lower = exclude_title.lower()
            logger.info(f"Filter: Excluding movie '{exclude_title}' from results")
            
            filtered = []
            for doc in results:
                doc_title = doc.metadata.get('title', '')
                doc_title_lower = doc_title.lower() if doc_title else ''
                
                # Exact match
                if doc_title_lower == exclude_lower:
                    logger.debug(f"Filter: Excluded '{doc_title}' (exact match)")
                    continue
                
                # Partial match check (in case title has variations)
                # Only exclude if the exclude_title is a complete word match
                if exclude_lower in doc_title_lower:
                    # Check if it's a word boundary match (avoid false positives)
                    # For "Home Alone", exclude "Home Alone" but not "Alone in Berlin"
                    if re.search(r'\b' + re.escape(exclude_lower) + r'\b', doc_title_lower):
                        logger.debug(f"Filter: Excluded '{doc_title}' (word boundary match)")
                        continue
                
                filtered.append(doc)
            
            # If filtering removed all results, return original results (edge case)
            if filtered:
                logger.info(f"Filter: Filtered {len(results)} results to {len(filtered)} (excluded '{exclude_title}')")
                return filtered
            else:
                logger.warning(f"Filter: Filtering removed all results, returning original results")
        
        return results
    
    def get_last_resolution_metadata(self):
        """Get resolution metadata from the last retrieve() call."""
        if hasattr(self.retriever, 'get_last_resolution_metadata'):
            return self.retriever.get_last_resolution_metadata()
        return None

    async def _arun(self, query: str) -> str:
        return self._run(query)


class PosterAnalysisArgs(BaseModel):
    image_path: str


class PosterAnalysisTool(BaseTool):
    name: str = "analyze_movie_poster"
    description: str = (
        "Use this tool when the user provides a movie poster image. "
        "Input should be a valid image path. Returns a visual description (caption) "
        "that you can use as a search query with movie_search to identify the movie."
    )
    vision_tool: Any = Field(default=None)

    args_schema: type[BaseModel] = PosterAnalysisArgs

    def _run(self, image_path: str) -> str:
        """
        Analyze poster and return caption as evidence.
        
        The agent should then call movie_search with this caption
        to identify the movie via semantic search.
        """
        try:
            response: PosterAnalysisResponse = self.vision_tool.analyze_poster(image_path)
            # Return the caption as evidence - agent will use it for movie_search
            # Format matches Colab approach: "Vision analysis says: '{caption}'"
            return (
                f"User uploaded a movie poster. Vision analysis says: '{response.caption}'. "
                f"Please search for movies that match this description using movie_search."
            )
        except Exception as e:
            return f"Failed to analyze poster: {str(e)}"

    async def _arun(self, image_path: str) -> str:
        return self._run(image_path)
