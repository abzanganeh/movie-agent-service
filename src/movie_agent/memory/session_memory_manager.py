"""
Session-based memory manager.

Manages separate memory instances per session ID.
Essential for multi-user scenarios and follow-up questions.
"""
from typing import Dict, Optional
from .memory_manager import MemoryManager
from .conversation_memory import ConversationMemory


class SessionMemoryManager:
    """
    Manages memory per session ID.
    
    Purpose:
    - Isolate conversation memory per user/session
    - Support follow-up questions ("that movie", "compare them")
    - Essential for quiz games (track game state per session)
    
    Key traits:
    - Session-based isolation
    - Automatic memory creation per session
    - Session cleanup support
    """
    
    def __init__(self, max_turns_per_session: int = 10):
        """
        Initialize session memory manager.
        
        :param max_turns_per_session: Maximum conversation turns per session
        """
        self._sessions: Dict[str, MemoryManager] = {}
        self._max_turns_per_session = max_turns_per_session
    
    def get_memory(self, session_id: str) -> MemoryManager:
        """
        Get or create memory for a session.
        
        Creates a new MemoryManager for the session if it doesn't exist.
        
        :param session_id: Unique session identifier
        :return: MemoryManager instance for this session
        """
        if session_id not in self._sessions:
            # Create new memory for this session
            conversation_memory = ConversationMemory(max_turns=self._max_turns_per_session)
            self._sessions[session_id] = MemoryManager(memories=[conversation_memory])
        return self._sessions[session_id]
    
    def record(self, session_id: str, event: Dict) -> None:
        """
        Record an event for a specific session.
        
        :param session_id: Session identifier
        :param event: Event dictionary to record
        """
        memory = self.get_memory(session_id)
        memory.record(event)
    
    def retrieve(self, session_id: str, query: str, k: int = 5) -> list:
        """
        Retrieve relevant events for a specific session.
        
        :param session_id: Session identifier
        :param query: Query string to search for
        :param k: Number of results to return
        :return: List of relevant events
        """
        memory = self.get_memory(session_id)
        return memory.retrieve(query, k=k)
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear memory for a specific session.
        
        Useful for session reset or logout.
        
        :param session_id: Session identifier
        """
        if session_id in self._sessions:
            self._sessions[session_id].clear()
            # Optionally remove the session entirely
            # del self._sessions[session_id]
    
    def clear_all(self) -> None:
        """Clear all sessions (useful for testing)."""
        for session_id in list(self._sessions.keys()):
            self.clear_session(session_id)
        self._sessions.clear()
    
    def get_conversation_memory(self, session_id: str) -> Optional[ConversationMemory]:
        """
        Get conversation memory for a session (convenience method).
        
        :param session_id: Session identifier
        :return: ConversationMemory instance or None
        """
        memory = self.get_memory(session_id)
        return memory.get_conversation_memory()
    
    def has_session(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        :param session_id: Session identifier
        :return: True if session exists, False otherwise
        """
        return session_id in self._sessions

