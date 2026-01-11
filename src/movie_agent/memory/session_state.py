"""
Session state management.

Tracks session-level state like quiz mode, active quiz context, etc.
"""
from typing import Dict, Optional, Any
from .quiz_state import QuizState


class SessionState:
    """
    Manages session-level state (mode, quiz context, etc.).
    """
    
    def __init__(self):
        """Initialize empty session state."""
        self.quiz_state: QuizState = QuizState()
        self.custom_state: Dict[str, Any] = {}  # Extensible state storage
    
    def get_quiz_state(self) -> QuizState:
        """Get quiz state object."""
        return self.quiz_state
    
    def is_quiz_mode(self) -> bool:
        """Check if session is in quiz mode."""
        return self.quiz_state.is_active()
    
    def has_active_quiz(self) -> bool:
        """Check if there's an active quiz."""
        return self.quiz_state.is_active()


class SessionStateManager:
    """
    Manages session state per session ID.
    
    Purpose:
    - Track quiz mode per session
    - Prevent quiz tool misuse
    - Enable state-aware agent behavior
    """
    
    def __init__(self):
        """Initialize session state manager."""
        self._states: Dict[str, SessionState] = {}
    
    def get_state(self, session_id: str) -> SessionState:
        """
        Get or create state for a session.
        
        :param session_id: Session identifier
        :return: SessionState instance
        """
        if session_id not in self._states:
            self._states[session_id] = SessionState()
        return self._states[session_id]
    
    def clear_state(self, session_id: str) -> None:
        """Clear state for a session."""
        if session_id in self._states:
            del self._states[session_id]
    
    def clear_all(self) -> None:
        """Clear all session states."""
        self._states.clear()

