"""
Chat orchestrator - read + decide path.

Reads from SessionContext and orchestrates chat interactions.
"""
from ..agent.tool_calling_agent import ToolCallingAgent
from ..context.session_context import SessionContext
from ..memory.session_state import SessionState


class ChatOrchestrator:
    """
    Orchestrates chat interactions.
    
    Read path: SessionContext → enrich message → agent
    
    OOP: Single Responsibility - orchestrates message enrichment with context.
    """
    
    def __init__(
        self,
        agent: ToolCallingAgent,
        session_context: SessionContext,
        session_state: SessionState,
    ):
        """
        Initialize chat orchestrator.
        
        :param agent: ToolCallingAgent instance
        :param session_context: SessionContext to read from
        :param session_state: SessionState for quiz awareness
        """
        self._agent = agent
        self._session_context = session_context
        self._session_state = session_state
    
    def enrich_message_with_context(self, user_message: str) -> str:
        """
        Enrich user message with session context.
        
        OOP: Orchestrates enrichment by delegating to specialized methods.
        
        :param user_message: Original user message
        :return: Enriched message with context
        """
        enriched = user_message
        
        if self._session_context.has_poster():
            poster = self._session_context.poster
            if poster.has_title():
                enriched = self._build_poster_context_with_title(poster, user_message)
            else:
                enriched = self._build_poster_context_without_title(poster, user_message)
        
        enriched = self._append_quiz_context(enriched)
        
        return enriched
    
    def _is_similarity_query(self, user_message: str) -> bool:
        """
        Detect if user is asking for similar movies.
        
        OOP: Single Responsibility - query classification logic.
        
        :param user_message: User's message
        :return: True if query is asking for similar movies
        """
        user_msg_lower = user_message.lower()
        similarity_phrases = ["like this", "similar to", "more like", "similar movies", "recommend movies"]
        return any(phrase in user_msg_lower for phrase in similarity_phrases)
    
    def _build_genre_query(self, poster) -> str | None:
        """
        Build genre-based query for similarity searches.
        
        OOP: Single Responsibility - query construction logic.
        
        Formats genres for optimal vector search matching (space-separated).
        
        :param poster: PosterContext with movie information
        :return: Genre-based query string or None
        """
        if poster.inferred_genres:
            # Join all genres with spaces for better vector search matching
            # Example: ["Comedy", "Family"] → "comedy family movies"
            genres_str = " ".join(poster.inferred_genres).lower()
            genre_query = f"{genres_str} movies"
        elif poster.mood:
            genre_query = f"{poster.mood} movies"
        else:
            return None
        
        # Note: Don't append title to query - it causes title-word matching
        # Instead, the instructions will tell LLM to exclude the original movie
        return genre_query
    
    def _build_poster_context_with_title(self, poster, user_message: str) -> str:
        """
        Build context instructions when poster title is identified.
        
        OOP: Single Responsibility - poster context construction.
        
        :param poster: PosterContext with title
        :param user_message: User's message
        :return: Enriched message with poster context
        """
        is_similarity_query = self._is_similarity_query(user_message)
        genre_query = self._build_genre_query(poster) if is_similarity_query else None
        
        context_parts = [
            f"POSTER CONTEXT (CRITICAL - USE THIS INFORMATION):",
            f"The user uploaded a movie poster that was identified as: '{poster.title}'",
            f"Genre/Mood: {poster.mood}",
        ]
        
        if poster.inferred_genres:
            context_parts.append(f"Genres: {', '.join(poster.inferred_genres)}")
        
        context_parts.extend([
            f"Visual description: {poster.caption}",
            f"",
            f"USER QUESTION: {user_message}",
            f"",
            f"INSTRUCTIONS:",
            f"- The poster shows the movie '{poster.title}'",
            f"- DO NOT call analyze_movie_poster tool (poster already analyzed)",
        ])
        
        if is_similarity_query and genre_query:
            context_parts.append(
                f"- CRITICAL: User wants SIMILAR movies by GENRE/MOOD, not just title similarity. "
                f"To find similar movies, you MUST:\n"
                f"  1. First, look up '{poster.title}' using movie_search to get its ACTUAL genres from the database\n"
                f"  2. Extract ALL genres from that movie's metadata (e.g., 'Comedy, Family' not just 'Comedy')\n"
                f"  3. Build a genre-based query using ALL genres with the format: '{genre_query} like {poster.title}'\n"
                f"     Example: If '{poster.title}' is 'Home Alone' with genres 'Comedy, Family', "
                f"use query: 'comedy family movies like Home Alone' (NOT just 'comedy movies')\n"
                f"  4. Search using movie_search with this query - the tool will automatically exclude '{poster.title}' from results"
            )
        else:
            fallback_genres = ', '.join(poster.inferred_genres) if poster.inferred_genres else poster.mood
            context_parts.append(
                f"- If user asks for similar movies, use movie_search with genre-based query using ALL genres. "
                f"First look up '{poster.title}' to get its actual genres from the database, then search using ALL genres "
                f"(e.g., '{fallback_genres} movies'), NOT just one genre or title similarity"
            )
        
        context_parts.append(
            f"- Always reference '{poster.title}' when answering questions about the uploaded poster"
        )
        
        return "\n".join(context_parts)
    
    def _build_poster_context_without_title(self, poster, user_message: str) -> str:
        """
        Build context instructions when poster title is not identified.
        
        OOP: Single Responsibility - poster context construction for unidentified posters.
        
        :param poster: PosterContext without title
        :param user_message: User's message
        :return: Enriched message with poster context
        """
        context_parts = [
            f"POSTER CONTEXT:",
            f"The user uploaded a movie poster, but no movie title was identified.",
            f"Visual description: {poster.caption}",
            f"Mood: {poster.mood}",
            f"",
            f"USER QUESTION: {user_message}",
            f"",
            f"INSTRUCTIONS:",
            f"- DO NOT call analyze_movie_poster tool again",
            f"- Use the visual description to help answer",
        ]
        
        return "\n".join(context_parts)
    
    def _append_quiz_context(self, enriched_message: str) -> str:
        """
        Append quiz state context if quiz is active.
        
        OOP: Single Responsibility - quiz context enrichment.
        
        :param enriched_message: Message already enriched with other context
        :return: Message with quiz context appended
        """
        quiz_state = self._session_state.get_quiz_state()
        if quiz_state.is_active():
            enriched_message += (
                f"\n\n[Session State: Quiz mode is ACTIVE (mode: {quiz_state.mode}, attempts: {quiz_state.attempts}). "
                "ONLY use check_quiz_answer when user is answering the quiz. "
                "NEVER start a new quiz unless explicitly requested.]"
            )
        
        return enriched_message
