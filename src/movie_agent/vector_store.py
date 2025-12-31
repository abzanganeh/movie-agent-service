from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS


class MovieVectorStore:
    def __init__(self, embedding_model, index_path: str):
        self._embedding_model = embedding_model
        self._index_path = index_path
        self._vectorstore: FAISS | None = None
    
    def build(self, documents: List[Document]) -> None:
        if not documents:
            raise ValueError("Cannot build vector store with empty documents.")
        self._vectorstore = FAISS.from_documents(
            documents=documents, 
            embedding=self._embedding_model
            )
        self._vectorstore.save_local(self._index_path)
    
    def load(self) -> None:
        self._vectorstore = FAISS.load_local(
            self._index_path,
            self._embedding_model,
            allow_dangerous_deserialization=True
        )

    def build_or_load(self, documents: List[Document]) -> None:
        try:
            self.load()
        except Exception:
            self.build(documents)

    def as_retriever(self, k: int = 5):
        if not self._vectorstore:
            raise RuntimeError("Vector store not initialized.")
        return self._vectorstore.as_retriever(
            search_kwargs={"k": k}
        )