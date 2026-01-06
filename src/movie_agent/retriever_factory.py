import os
from typing import Optional
from .tools.movie_retriever import MovieRetriever
from .vector_store import MovieVectorStore
from .data_loader import MovieDataLoader
from .canonicalizer import build_documents
from .chunking import MovieChunker
from .config import MovieAgentConfig
from .resolution import VocabularyBuilder, MovieTitleResolver


def create_retriever(
    config: Optional[MovieAgentConfig] = None,
    embedding_model=None,
    vector_store: Optional[MovieVectorStore] = None,
    title_resolver: Optional[MovieTitleResolver] = None,
) -> MovieRetriever:
    """
    Factory function to create a configured MovieRetriever instance.
    
    Handles:
    - Embedding model creation
    - Vector store initialization
    - Index building if needed
    - Retriever creation
    
    :param config: MovieAgentConfig instance
    :param embedding_model: Embedding model instance (created from env if None)
    :param vector_store: Pre-initialized MovieVectorStore (optional)
    :return: Configured MovieRetriever instance
    """
    # Create embedding model if not provided
    if embedding_model is None:
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        
        if embedding_provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            from .config_validator import get_required_env
            api_key = get_required_env(
                "OPENAI_API_KEY",
                description="OpenAI API key for embeddings (get from https://platform.openai.com/api-keys)"
            )
            embedding_model = OpenAIEmbeddings(openai_api_key=api_key)
        elif embedding_provider == "huggingface":
            raise NotImplementedError("HuggingFace embeddings not yet implemented")
        else:
            raise ValueError(f"Unknown embedding provider: {embedding_provider}")
    
    # Get index path
    index_path = config.faiss_index_path if config else os.getenv(
        "VECTOR_STORE_PATH", 
        "movie_vectorstore"
    )
    
    if not index_path:
        raise ValueError(
            "FAISS index path must be provided via config.faiss_index_path "
            "or VECTOR_STORE_PATH env var"
        )
    
    # Create or use provided vector store
    if vector_store is None:
        vector_store = MovieVectorStore(
            embedding_model=embedding_model,
            index_path=index_path
        )
        
        # Build or load index
        if not os.path.exists(index_path):
            if config is None or not config.movies_csv_path:
                raise ValueError(
                    "Cannot build index: movies_csv_path not provided in config"
                )
            
            # Load and process movies
            loader = MovieDataLoader(config.movies_csv_path)
            movies = loader.load_movies()
            documents = build_documents(movies)
            
            # Chunk documents
            chunker = MovieChunker()
            chunked_docs = chunker.chunk(documents)
            
            # Build index
            vector_store.build(chunked_docs)
        else:
            # Load existing index
            vector_store.load()
    
    # Create retriever (implements RetrieverTool protocol directly)
    # Title resolver is optional - if provided, enables query correction and entity normalization
    return MovieRetriever(vector_store=vector_store, k=5, title_resolver=title_resolver)