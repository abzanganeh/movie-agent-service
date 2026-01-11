"""
Memory manager for composing multiple memory systems.

Follows Open-Closed Principle: extensible without modification.
"""
from typing import List, Dict, Any, Optional
from .agent_memory import AgentMemory
from .conversation_memory import ConversationMemory


class MemoryManager:
    """
    Composes multiple memory systems.
    
    Memory is infrastructure, not behavior.
    This allows:
    - Multiple memory types (conversation, semantic, episodic)
    - Extensibility without modification (OCP)
    - Testability (each memory can be tested independently)
    """
    
    def __init__(self, memories: Optional[List[AgentMemory]] = None):
        """
        Initialize memory manager.
        
        :param memories: List of memory implementations to compose
        """
        self._memories: List[AgentMemory] = memories or []
    
    def add_memory(self, memory: AgentMemory) -> None:
        """Add a memory system to the manager."""
        self._memories.append(memory)
    
    def record(self, event: Dict[str, Any]) -> None:
        """
        Record an event in all memory systems.
        
        :param event: Event dictionary to record
        """
        for memory in self._memories:
            try:
                memory.record(event)
            except Exception:
                # Fail soft - one memory failure shouldn't break the system
                pass
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant events from all memory systems.
        
        :param query: Query string to search for
        :param k: Number of results per memory system
        :return: Combined list of events from all memory systems
        """
        results: List[Dict[str, Any]] = []
        for memory in self._memories:
            try:
                results.extend(memory.retrieve(query, k=k))
            except Exception:
                # Fail soft
                pass
        return results
    
    def clear(self) -> None:
        """Clear all memory systems."""
        for memory in self._memories:
            try:
                memory.clear()
            except Exception:
                # Fail soft
                pass
    
    def get_conversation_memory(self) -> Optional[ConversationMemory]:
        """
        Get conversation memory instance if available.
        
        Convenience method for accessing conversation-specific functionality.
        
        :return: ConversationMemory instance or None
        """
        for memory in self._memories:
            if isinstance(memory, ConversationMemory):
                return memory
        return None

