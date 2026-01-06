"""
Session context manager.

Manages SessionContext instances per session ID.
"""
from typing import Dict
from .session_context import SessionContext


class SessionContextManager:
    """
    Manages session context per session ID.
    
    Purpose:
    - Single source of truth for session state
    - Isolate context per user/session
    - Clean domain model (no Flask, no LangChain)
    """
    
    def __init__(self):
        """Initialize context manager."""
        self._contexts: Dict[str, SessionContext] = {}
    
    def get_context(self, session_id: str) -> SessionContext:
        """
        Get or create context for a session.
        
        :param session_id: Session identifier
        :return: SessionContext instance
        """
        if session_id not in self._contexts:
            self._contexts[session_id] = SessionContext()
        return self._contexts[session_id]
    
    def clear_context(self, session_id: str) -> None:
        """Clear context for a session."""
        if session_id in self._contexts:
            self._contexts[session_id].clear_poster()
    
    def clear_all(self) -> None:
        """Clear all contexts."""
        self._contexts.clear()


