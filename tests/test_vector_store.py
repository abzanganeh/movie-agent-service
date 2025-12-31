import pytest
from langchain_core.documents import Document
from src.movie_agent.vector_store import MovieVectorStore
from langchain.embeddings.base import Embeddings

class FakeEmbedding(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 10 for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 10

@pytest.fixture
def documents():
    return [
        Document(page_content="Title: Inception.", metadata={"title": "Inception"}),
        Document(page_content="Title: Matrix.", metadata={"title": "Matrix"}),
    ]

def test_build_and_retrieve(tmp_path, documents):
    embedding = FakeEmbedding()
    store = MovieVectorStore(
        embedding_model=embedding,
        index_path=str(tmp_path / "faiss_index")
    )

    # Build index
    store.build(documents)

    # Retrieve
    retriever = store.as_retriever(k=1)
    results = retriever.get_relevant_documents("dream")

    assert len(results) == 1
    assert "Title:" in results[0].page_content
