from typing import Protocol, List
from langchain_core.documents import Document


class RetrieverTool(Protocol):
    """Protocol for a retrieval tool used by the agent."""
    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        ...



# Placeholder for concrete implementations

