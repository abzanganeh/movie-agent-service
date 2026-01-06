from langchain_core.documents import Document
from src.movie_agent.chunking import MovieChunker

def test_chunking_splits_documents():
    docs = [
        Document(page_content="A " * 500, metadata={"id": 1})
    ]

    chunker = MovieChunker(chunk_size=100, chunk_overlap=10)
    chunks = chunker.chunk(docs)

    assert len(chunks) > 1
    assert all(isinstance(c, Document) for c in chunks)
