from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class MovieChunker:
    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 50):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
    def chunk(self, documents: List[Document]) -> List[Document]:
        if not documents:
            return []
        return self._splitter.split_documents(documents)