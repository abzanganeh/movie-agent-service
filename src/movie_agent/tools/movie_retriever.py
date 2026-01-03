from typing import List
from langchain_core.documents import Document
from .retriever_tool import RetrieverTool  # protocol
from ..vector_store import MovieVectorStore


class MovieRetriever(RetrieverTool):
    """
    Retrieval layer for movie search.
    
    Single Responsibility: Retrieve documents matching queries.
    Implements RetrieverTool protocol directly.
    
    Uses MovieVectorStore for storage (composition, not inheritance).
    """
    
    def __init__(self, vector_store: MovieVectorStore, k: int = 5):
        """
        :param vector_store: MovieVectorStore instance (must be initialized)
        :param k: Default number of results to return
        """
        if not vector_store.is_initialized():
            raise RuntimeError(
                "MovieVectorStore must be initialized (call build() or load()) "
                "before creating MovieRetriever"
            )
        self._vector_store = vector_store
        self._default_k = k

    def retrieve(self, query: str, k: int = None) -> List[Document]:
        """
        Retrieve top-k movies matching the query.
        
        Implements RetrieverTool protocol.
        """
        k = k or self._default_k
        
        # Use MovieVectorStore's underlying LangChain FAISS
        langchain_vectorstore = self._vector_store.get_langchain_vectorstore()
        langchain_retriever = langchain_vectorstore.as_retriever(
            search_kwargs={"k": k}
        )
        
        return langchain_retriever.get_relevant_documents(query)