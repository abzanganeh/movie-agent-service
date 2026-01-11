"""
Poster Orchestration Service

Handles the multi-step workflow for poster analysis:
1. Vision tool → caption
2. Retriever → movie search results
3. Synthesis → title, mood, confidence
"""

from typing import Optional
import re
import logging
from ..tools.vision_tool import VisionTool
from ..tools.movie_retriever import MovieRetriever
from ..schemas import PosterAnalysisResponse
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class PosterOrchestrationService:
    """
    Orchestrates poster analysis workflow.
    """
    
    def __init__(
        self,
        vision_tool: VisionTool,
        retriever: MovieRetriever,
    ):
        """
        :param vision_tool: VisionTool instance for caption generation
        :param retriever: MovieRetriever instance for semantic search
        """
        self.vision_tool = vision_tool
        self.retriever = retriever
    
    @staticmethod
    def _extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
        """
        Extract unique significant keywords from text.
        
        Filters out stop words and short words, removes duplicates.
        This is a utility method used for both search query enhancement and title matching.
        
        :param text: Input text to extract keywords from
        :param max_keywords: Maximum number of keywords to return
        :return: List of unique keywords
        """
        text_lower = text.lower()
        stop_words = {
            'movie', 'poster', 'image', 'picture', 'photo', 'film',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
            'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'
        }
        words = text_lower.split()
        unique_keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = [w for w in unique_keywords if not (w in seen or seen.add(w))]
        
        return unique_keywords[:max_keywords]
    
    def analyze(self, image_path: str) -> PosterAnalysisResponse:
        """
        Analyze a movie poster and return structured response.
        
        Workflow:
        1. Generate caption from vision tool
        2. Search for movies using caption as query
        3. Synthesize title, mood, confidence from results
        
        :param image_path: Path to poster image file
        :return: PosterAnalysisResponse with title, mood, confidence, caption
        """
        # Step 1: Vision → caption
        vision_response = self.vision_tool.analyze_poster(image_path)
        caption = vision_response.caption
        logger.info(f"Poster orchestration - Caption: {caption}")
        
        # Step 2: Semantic search → movie candidates
        # Enhance caption for better search by extracting key terms
        # Remove repetitive words and focus on unique keywords
        unique_keywords = self._extract_keywords(caption, max_keywords=5)
        
        # Build enhanced query: prioritize movie title keywords
        # If we have a strong keyword (like "hangover"), use it directly as a movie title search
        if unique_keywords:
            # Use the most significant keyword (first one) as primary search term
            primary_keyword = unique_keywords[0]
            # Build query: "primary_keyword movie" for better title matching
            enhanced_query = f"{primary_keyword} movie"
            
            # If we have multiple keywords, add them for context (but primary keyword is most important)
            if len(unique_keywords) > 1:
                additional_keywords = ' '.join(unique_keywords[1:3])  # Limit to 2 additional
                enhanced_query = f"{primary_keyword} {additional_keywords} movie"
        else:
            # Fallback: use original caption
            enhanced_query = caption
            if "movie" not in caption.lower():
                enhanced_query = f"{caption} movie"
        
        logger.debug(f"Poster orchestration - Original caption: {caption}")
        logger.debug(f"Poster orchestration - Extracted keywords: {unique_keywords}")
        logger.debug(f"Poster orchestration - Enhanced query: {enhanced_query}")
        
        # Use k=5 to get more candidates for better title/mood inference
        search_results = self.retriever.retrieve(enhanced_query, k=5)
        logger.info(f"Poster orchestration - Found {len(search_results)} search results for caption: '{caption}'")
        
        # Log first few results for debugging
        for i, result in enumerate(search_results[:5]):
            title_from_meta = result.metadata.get('title', 'N/A') if hasattr(result, 'metadata') and result.metadata else 'N/A'
            page_preview = result.page_content[:150] if hasattr(result, 'page_content') else 'N/A'
            logger.info(f"Poster orchestration - Result {i+1}: title={title_from_meta}, page_content_preview={page_preview}")
        
        # Step 3: Synthesize results
        title = self._extract_title(search_results, caption)
        # Pass the identified title to mood inference for better accuracy
        mood = self._infer_mood(search_results, caption, vision_response.mood, identified_title=title)
        confidence = self._calculate_confidence(search_results, caption)
        
        logger.info(f"Poster orchestration - Final: title={title}, mood={mood}, confidence={confidence}")
        
        return PosterAnalysisResponse(
            caption=caption,
            title=title,
            mood=mood,
            confidence=confidence,
            inferred_genres=vision_response.inferred_genres,  # Keep from vision tool
        )
    
    def _extract_title(self, search_results: list[Document], caption: str) -> Optional[str]:
        """
        Extract movie title from search results, prioritizing titles that match caption keywords.
        
        Strategy:
        1. Extract all candidate titles from top results
        2. Score each title based on keyword matches with caption
        3. Return the best matching title, or first result if no matches
        
        :param search_results: List of Document objects from retriever
        :param caption: Visual caption from vision tool (for keyword matching)
        :return: Movie title string or None
        """
        if not search_results:
            logger.warning("No search results to extract title from")
            return None
        
        # Extract candidate titles from top 5 results
        candidates = []
        caption_lower = caption.lower()  # Needed for substring matching
        
        # Extract keywords from caption for matching (reuse utility method)
        caption_keywords = set(self._extract_keywords(caption, max_keywords=10))
        logger.debug(f"Caption keywords for title matching: {caption_keywords}")
        
        for i, result in enumerate(search_results[:5]):  # Check top 5 results
            title = None
            
            # Priority 1: Get title from metadata (most reliable)
            if hasattr(result, 'metadata') and result.metadata:
                title = result.metadata.get('title') or result.metadata.get('Title')
                if title:
                    title_str = str(title).strip()
                    if title_str:
                        candidates.append((title_str, i))
                        continue
            
            # Priority 2: Extract from page_content (format: "Title: The Hangover. Year: 2009. Genres: Comedy, ...")
            if not title and hasattr(result, 'page_content') and result.page_content:
                content = result.page_content
                title_match = re.search(r'Title:\s*([^.]+)', content, re.IGNORECASE)
                if title_match:
                    title_str = title_match.group(1).strip()
                    if title_str:
                        candidates.append((title_str, i))
        
        if not candidates:
            logger.warning(f"Could not extract any titles from search results")
            return None
        
        # Score candidates based on keyword matches with caption
        scored_candidates = []
        for title, rank in candidates:
            title_lower = title.lower()
            # Extract words from title (split on spaces and punctuation)
            title_words = set(re.findall(r'\b\w+\b', title_lower))
            title_words = {w for w in title_words if len(w) > 3}  # Filter short words
            
            # Calculate match score
            # 1. Exact word matches (highest weight) - e.g., "hangover" in caption matches "hangover" in title
            exact_matches = len(caption_keywords.intersection(title_words))
            
            # 2. Substring matches (lower weight, but only if keyword is a complete word in title)
            # Check if any caption keyword appears as a complete word in the title
            # Use word boundaries to avoid false positives like "hangman" matching "hangover"
            substring_matches = 0
            for kw in caption_keywords:
                # Check if keyword appears as a complete word in title (using word boundaries)
                if re.search(r'\b' + re.escape(kw) + r'\b', title_lower):
                    substring_matches += 1
                # Also check if title word appears in caption (for cases like "The Hangover")
                elif any(tw in caption_lower for tw in title_words if len(tw) > 3):
                    substring_matches += 0.5  # Lower weight for reverse match
            
            # 3. Rank bonus (lower rank = higher score, but much smaller weight)
            rank_bonus = (5 - rank) * 0.05
            
            # Calculate final score with strong preference for exact matches
            score = exact_matches * 5.0 + substring_matches * 1.0 + rank_bonus
            scored_candidates.append((title, score, rank))
            logger.debug(f"Title candidate: '{title}' (rank {rank+1}) - score: {score:.2f} (exact={exact_matches}, substring={substring_matches:.1f}, rank_bonus={rank_bonus:.2f})")
        
        # Sort by score (descending), then by rank (ascending)
        scored_candidates.sort(key=lambda x: (-x[1], x[2]))
        
        best_title, best_score, best_rank = scored_candidates[0]
        logger.info(f"Title extracted: '{best_title}' (rank {best_rank+1}, score: {best_score:.2f})")
        
        # If best match has a reasonable score, return it; otherwise return first result
        if best_score >= 1.0 or len(candidates) == 1:
            return best_title
        else:
            # Return first result if no good matches (fallback to semantic search ranking)
            first_title = candidates[0][0]
            logger.info(f"No strong keyword match found, using first result: '{first_title}'")
            return first_title
    
    @staticmethod
    def _extract_genres_from_result(result: Document) -> list[str]:
        """
        Extract genres from a search result document.
        
        :param result: Document object from retriever
        :return: List of genre strings (lowercase)
        """
        genres = []
        
        # Priority 1: Extract from page_content (format: "Genres: Comedy, Drama")
        if hasattr(result, 'page_content') and result.page_content:
            content = result.page_content
            genres_match = re.search(r'Genres?:\s*([^.]+)', content, re.IGNORECASE)
            if genres_match:
                genres_part = genres_match.group(1)
                genres_list = [g.strip().lower() for g in genres_part.split(',')]
                genres_list = [g for g in genres_list if g]  # Filter empty
                genres.extend(genres_list)
        
        # Priority 2: Extract from metadata
        if hasattr(result, 'metadata') and result.metadata:
            genre = (
                result.metadata.get('Genre') or 
                result.metadata.get('genre') or
                result.metadata.get('Genres') or
                result.metadata.get('genres')
            )
            if genre:
                if isinstance(genre, str):
                    genres_list = [g.strip().lower() for g in genre.split(',')]
                    genres.extend(genres_list)
                elif isinstance(genre, list):
                    genres.extend([g.lower() if isinstance(g, str) else str(g).lower() for g in genre])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_genres = []
        for g in genres:
            if g not in seen:
                seen.add(g)
                unique_genres.append(g)
        
        return unique_genres
    
    def _infer_mood(
        self,
        search_results: list[Document],
        caption: str,
        vision_mood: str,
        identified_title: Optional[str] = None
    ) -> str:
        """
        Infer mood from search results and visual description.
        
        Uses a rule-based approach that blends:
        1. Genres from the identified movie (highest priority)
        2. Genres from top search results (weighted by rank)
        3. BLIP caption keywords (secondary signal)
        4. Plot summary keywords (if available)
        
        :param search_results: List of Document objects from retriever
        :param caption: Visual caption from vision tool
        :param vision_mood: Mood inferred by vision tool (fallback)
        :param identified_title: The movie title that was identified (if any)
        :return: Synthesized mood string
        """
        caption_lower = caption.lower()
        
        # Step 1: Check genres from search results (strongest signal)
        if search_results:
            # Collect genres with weights (prioritize identified title and top results)
            genre_weights = {}  # genre -> total weight
            plot_keywords = []
            
            # First, try to find the identified title in results (highest priority)
            identified_genres = []
            if identified_title:
                identified_title_lower = identified_title.lower()
                for i, result in enumerate(search_results):
                    result_title = None
                    # Get title from metadata
                    if hasattr(result, 'metadata') and result.metadata:
                        result_title = result.metadata.get('title') or result.metadata.get('Title')
                    # Or extract from page_content
                    if not result_title and hasattr(result, 'page_content') and result.page_content:
                        title_match = re.search(r'Title:\s*([^.]+)', result.page_content, re.IGNORECASE)
                        if title_match:
                            result_title = title_match.group(1).strip()
                    
                    # Check if this result matches the identified title
                    if result_title and result_title.lower() == identified_title_lower:
                        # Extract genres from this specific movie (highest weight)
                        genres = self._extract_genres_from_result(result)
                        identified_genres = genres
                        logger.info(f"Mood inference - Found identified title '{identified_title}' in result {i+1}, genres: {genres}")
                        break
            
            # Collect genres from all top results (weighted by rank)
            for i, result in enumerate(search_results[:5]):  # Check top 5 results
                # Weight: first result = 3.0, second = 2.0, third = 1.5, etc.
                weight = max(1.0, 4.0 - i * 0.5)
                
                # If this is the identified title, give it extra weight
                result_title = None
                if hasattr(result, 'metadata') and result.metadata:
                    result_title = result.metadata.get('title') or result.metadata.get('Title')
                if result_title and identified_title and result_title.lower() == identified_title.lower():
                    weight = 10.0  # Much higher weight for identified title
                
                genres = self._extract_genres_from_result(result)
                for genre in genres:
                    genre_clean = genre.strip().lower()
                    if genre_clean:
                        genre_weights[genre_clean] = genre_weights.get(genre_clean, 0) + weight
                
                logger.debug(f"Result {i+1} genres: {genres}, weight: {weight}")
            
            # Log weighted genres for debugging
            if genre_weights:
                sorted_genres = sorted(genre_weights.items(), key=lambda x: -x[1])
                logger.info(f"Mood inference - Weighted genres: {sorted_genres[:5]}")
            
            # Prioritize identified title's genres if found
            if identified_genres:
                all_genres = identified_genres
            else:
                # Use weighted genres (sort by weight, take top genres)
                all_genres = [g for g, w in sorted(genre_weights.items(), key=lambda x: -x[1])]
            
            logger.info(f"Mood inference - Final genre list (prioritized): {all_genres[:5]}")
            
            # Genre-based mood inference (priority order - check individual genres)
            # Check each genre individually for more accurate matching
            for genre in all_genres:
                genre_clean = genre.strip().lower()
                # Comedy takes highest priority (most specific)
                if 'comedy' in genre_clean:
                    logger.info(f"Mood inference - Matched 'comedy' in genre '{genre_clean}' → Comedic")
                    return "Comedic"
                # Horror/Dark genres
                if any(g in genre_clean for g in ['horror', 'thriller', 'suspense', 'mystery']):
                    logger.info(f"Mood inference - Matched dark genre '{genre_clean}' → Dark")
                    return "Dark"
                # Action/Adventure/Thrilling
                if any(g in genre_clean for g in ['action', 'adventure']):
                    logger.info(f"Mood inference - Matched action/adventure genre '{genre_clean}' → Thrilling")
                    return "Thrilling"
                # Romance
                if 'romance' in genre_clean or 'romantic' in genre_clean:
                    logger.info(f"Mood inference - Matched romance genre '{genre_clean}' → Romantic")
                    return "Romantic"
                # Drama (but not comedy-drama, which we already handled)
                if 'drama' in genre_clean and 'comedy' not in genre_clean:
                    logger.info(f"Mood inference - Matched drama genre '{genre_clean}' → Dramatic")
                    return "Dramatic"
                # Sci-fi/Fantasy
                if any(g in genre_clean for g in ['sci-fi', 'science fiction', 'fantasy']):
                    logger.info(f"Mood inference - Matched sci-fi/fantasy genre '{genre_clean}' → Thrilling")
                    return "Thrilling"  # Sci-fi often has thrilling elements
            
            # If no specific genre match, check combined genre string
            genre_str = ' '.join(all_genres)
            if 'comedy' in genre_str:
                return "Comedic"
            elif any(g in genre_str for g in ['horror', 'thriller', 'suspense']):
                return "Dark"
            elif any(g in genre_str for g in ['action', 'adventure']):
                return "Thrilling"
            elif 'romance' in genre_str or 'romantic' in genre_str:
                return "Romantic"
            elif 'drama' in genre_str:
                return "Dramatic"
        
        # Step 2: BLIP caption keyword analysis (secondary signal - only if no genre match)
        # Use caption keywords as fallback when genres don't provide clear signal
        # Thrilling keywords
        thrilling_keywords = [
            'fight', 'chase', 'building', 'danger', 'cityscape', 'action',
            'explosion', 'gun', 'weapon', 'battle', 'war', 'combat',
            'running', 'jumping', 'falling', 'crash', 'fire', 'smoke'
        ]
        if any(kw in caption_lower for kw in thrilling_keywords):
            return "Thrilling"
        
        # Comedic keywords (be careful - "hangover" might trigger false positives)
        # Only match if it's clearly comedic context
        comedic_keywords = [
            'funny', 'smile', 'laugh', 'comedy', 'humor', 'joke',
            'silly', 'wacky', 'goofy', 'cartoon', 'animated', 'comic'
        ]
        # Check if caption has comedic context (not just the word "hangover")
        if any(kw in caption_lower for kw in comedic_keywords):
            return "Comedic"
        
        # Dark keywords (be careful - "dark" can be literal color description)
        # Remove generic words that could be false positives
        dark_keywords = [
            'blood', 'horror', 'scary', 'frightening', 'gloomy', 
            'ominous', 'sinister', 'terror', 'fear'
        ]
        if any(kw in caption_lower for kw in dark_keywords):
            return "Dark"
        
        # Romantic keywords
        romantic_keywords = [
            'couple', 'romance', 'love', 'kiss', 'heart', 'wedding',
            'romantic', 'together', 'embrace', 'holding hands'
        ]
        if any(kw in caption_lower for kw in romantic_keywords):
            return "Romantic"
        
        # Dramatic keywords
        dramatic_keywords = [
            'serious', 'intense', 'emotional', 'dramatic', 'tension',
            'confrontation', 'struggle', 'conflict'
        ]
        if any(kw in caption_lower for kw in dramatic_keywords):
            return "Dramatic"
        
        # Step 3: Fallback to vision tool's mood
        if vision_mood and vision_mood != "Unknown" and vision_mood != "Neutral":
            return vision_mood
        
        # Step 4: Default
        return "Neutral"
    
    def _calculate_confidence(
        self,
        search_results: list[Document],
        caption: str
    ) -> float:
        """
        Calculate confidence score based on search results quality.
        
        :param search_results: List of Document objects from retriever
        :param caption: Visual caption from vision tool
        :return: Confidence score (0.0-1.0)
        """
        if not search_results:
            return 0.0
        
        # If we have results, base confidence on:
        # 1. Number of results (more = higher confidence)
        # 2. Quality of first match (if title matches caption keywords)
        
        num_results = len(search_results)
        if num_results >= 3:
            base_confidence = 0.8
        elif num_results >= 2:
            base_confidence = 0.6
        else:
            base_confidence = 0.4
        
        # Check if first result title appears in caption (higher confidence)
        first_result = search_results[0]
        if hasattr(first_result, 'metadata') and first_result.metadata:
            title = first_result.metadata.get('Title') or first_result.metadata.get('title')
            if title:
                title_lower = str(title).lower()
                caption_lower = caption.lower()
                # If title keywords appear in caption, boost confidence
                title_words = title_lower.split()
                if any(word in caption_lower for word in title_words if len(word) > 3):
                    return min(0.9, base_confidence + 0.1)
        
        return base_confidence

