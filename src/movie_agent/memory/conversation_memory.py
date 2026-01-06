"""
Conversation memory implementation.

Short-term, bounded memory for conversational continuity.
FIFO buffer - no embeddings, no persistence.
"""
from typing import List, Dict, Any
from .agent_memory import AgentMemory


class ConversationMemory(AgentMemory):
    """
    Conversation memory for short-term conversational continuity.
    
    Purpose:
    - Maintain conversational continuity
    - Resolve pronouns ("that movie", "compare them")
    - Keep last N turns in memory
    
    Key traits:
    - FIFO (first in, first out)
    - No embeddings
    - No persistence
    - Cheap and predictable
    """
    
    def __init__(self, max_turns: int = 10):
        """
        Initialize conversation memory.
        
        :param max_turns: Maximum number of conversation turns to keep
        """
        self._buffer: List[Dict[str, Any]] = []
        self._max_turns = max_turns
    
    def record(self, event: Dict[str, Any]) -> None:
        """
        Record a conversation event.
        
        :param event: Event dictionary (should contain 'type' and 'content')
        """
        self._buffer.append(event)
        # Enforce max_turns limit (FIFO eviction)
        if len(self._buffer) > self._max_turns:
            self._buffer = self._buffer[-self._max_turns:]
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversation events.
        
        Returns the most recent k events (query string is ignored for simplicity).
        For conversation memory, recency is more important than semantic similarity.
        
        :param query: Query string (ignored - returns recent events)
        :param k: Number of recent events to return
        :return: List of recent event dictionaries
        """
        return self._buffer[-k:] if self._buffer else []
    
    def clear(self) -> None:
        """Clear all conversation history."""
        self._buffer.clear()
    
    def get_recent_turns(self, k: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversation turns (convenience method).
        
        :param k: Number of turns to return
        :return: List of recent event dictionaries
        """
        return self.retrieve("", k=k)
    
    def format_as_chat_history(self) -> str:
        """
        Format conversation history as a chat history string.
        
        Useful for injecting into prompts.
        
        :return: Formatted chat history string
        """
        if not self._buffer:
            return ""
        
        lines = []
        for event in self._buffer:
            event_type = event.get("type", "unknown")
            content = event.get("content", "")
            role = event.get("role", "user")
            
            if event_type == "user_query":
                lines.append(f"User: {content}")
            elif event_type == "assistant_response":
                lines.append(f"Assistant: {content}")
            elif role:
                lines.append(f"{role.title()}: {content}")
            else:
                lines.append(content)
        
        return "\n".join(lines)

