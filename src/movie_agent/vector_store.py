from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS


class MovieVectorStore:
    """
    Storage layer for FAISS vector index.
    
    Single Responsibility: Build, load, and save vector indexes.
    Does NOT handle retrieval - that's a separate concern.
    """
    
    def __init__(self, embedding_model, index_path: str):
        self._embedding_model = embedding_model
        self._index_path = index_path
        self._vectorstore: FAISS | None = None
    
    def build(self, documents: List[Document]) -> None:
        """Build FAISS index from documents."""
        if not documents:
            raise ValueError("Cannot build vector store with empty documents.")
        self._vectorstore = FAISS.from_documents(
            documents=documents, 
            embedding=self._embedding_model
        )
        self._vectorstore.save_local(self._index_path)
    
    def load(self) -> None:
        """Load existing FAISS index from disk."""
        self._vectorstore = FAISS.load_local(
            self._index_path,
            self._embedding_model,
            allow_dangerous_deserialization=True
        )

    def build_or_load(self, documents: List[Document]) -> None:
        """Build index if missing, otherwise load existing."""
        try:
            self.load()
        except Exception:
            self.build(documents)
    
    def is_initialized(self) -> bool:
        """Check if vector store is initialized."""
        return self._vectorstore is not None
    
    def get_langchain_vectorstore(self) -> FAISS:
        """
        Get underlying LangChain FAISS instance.
        
        This is for internal use by MovieRetriever only.
        Not part of public API - retrieval should use MovieRetriever.
        """
        if not self._vectorstore:
            raise RuntimeError("Vector store not initialized. Call build() or load() first.")
        return self._vectorstore