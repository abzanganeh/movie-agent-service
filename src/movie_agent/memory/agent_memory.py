"""
Memory protocol definition.

Follows the same pattern as RetrieverTool and VisionTool protocols.
Memory is infrastructure, not behavior.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class AgentMemory(ABC):
    """
    Protocol for agent memory systems.
    
    Memory responsibilities:
    - Store structured interaction facts
    - Provide retrieval interfaces
    - Apply retention and eviction policies
    
    Memory must NOT:
    - Decide tool usage
    - Format prompts
    - Store raw LLM transcripts blindly
    """
    
    @abstractmethod
    def record(self, event: Dict[str, Any]) -> None:
        """
        Record an interaction event.
        
        :param event: Dictionary containing event data (type, content, metadata, etc.)
        """
        pass
    
    @abstractmethod
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memory events.
        
        :param query: Query string to search for
        :param k: Number of results to return
        :return: List of event dictionaries
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all stored memories."""
        pass

