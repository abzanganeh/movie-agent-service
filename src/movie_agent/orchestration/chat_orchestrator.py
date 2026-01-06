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
        
        :param user_message: Original user message
        :return: Enriched message with context
        """
        enriched = user_message
        
        if self._session_context.has_poster():
            poster = self._session_context.poster
            if poster.has_title():
                context_parts = [
                    f"POSTER CONTEXT (CRITICAL - USE THIS INFORMATION):",
                    f"The user uploaded a movie poster that was identified as: '{poster.title}'",
                    f"Genre/Mood: {poster.mood}",
                    f"Visual description: {poster.caption}",
                    f"",
                    f"USER QUESTION: {user_message}",
                    f"",
                    f"INSTRUCTIONS:",
                    f"- The poster shows the movie '{poster.title}'",
                    f"- DO NOT call analyze_movie_poster tool (poster already analyzed)",
                    f"- If user asks for similar movies, use movie_search with query like '{poster.title}' or '{poster.mood} movies'",
                    f"- Always reference '{poster.title}' when answering questions about the uploaded poster",
                ]
            else:
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
            
            enriched = "\n".join(context_parts)
        
        quiz_state = self._session_state.get_quiz_state()
        if quiz_state.is_active():
            enriched += (
                f"\n\n[Session State: Quiz mode is ACTIVE (mode: {quiz_state.mode}, attempts: {quiz_state.attempts}). "
                "ONLY use check_quiz_answer when user is answering the quiz. "
                "NEVER start a new quiz unless explicitly requested.]"
            )
        
        return enriched
