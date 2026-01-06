"""
Public application facade for Movie Agent Service.

This is the single stable entry point for the library.
All internal structure can change freely, but this API remains stable.
"""
import os
from pathlib import Path
from typing import Optional
from .config import MovieAgentConfig
from .schemas import ChatResponse, PosterAnalysisResponse
from .service import MovieAgentService
from .llm_factory import get_llm_instance
from .vision_factory import create_vision_tool
from .retriever_factory import create_retriever
from .resolution import create_title_resolver
from .vector_store import MovieVectorStore
from .data_loader import MovieDataLoader
from .canonicalizer import build_documents
from .chunking import MovieChunker


class MovieAgentApp:
    """
    Public application facade for Movie Agent Service.
    
    This is the single stable entry point for clients.
    All dependency wiring and factory usage is encapsulated here.
    
    Usage:
        config = MovieAgentConfig(...)
        app = MovieAgentApp(config)
        app.initialize()
        response = app.chat("Find sci-fi movies")
    """
    
    def __init__(self, config: MovieAgentConfig):
        """
        Initialize the application facade.
        
        :param config: MovieAgentConfig instance
        """
        self._config = config
        self._service: Optional[MovieAgentService] = None
    
    def initialize(self) -> None:
        """
        Initialize the service and wire all dependencies.
        
        This method:
        - Resolves relative paths relative to service directory
        - Builds vector store if needed
        - Creates semantic resolver
        - Creates retriever and vision tools
        - Creates LLM instance
        - Wires everything to the service
        - Warms up the service
        
        Call this once before using chat() or analyze_poster().
        """
        if self._service:
            return
        
        # Resolve relative paths relative to service directory (not caller's CWD)
        # This ensures paths work regardless of where the code is called from
        service_dir = Path(__file__).parent.parent.parent  # movie-agent-service/
        
        # Resolve movies CSV path
        if not os.path.isabs(self._config.movies_csv_path):
            resolved_movies_path = str(service_dir / self._config.movies_csv_path)
            self._config.movies_csv_path = resolved_movies_path
        
        # Resolve FAISS index path (provide default if None)
        if not self._config.faiss_index_path:
            # Default to service directory / movie_vectorstore
            self._config.faiss_index_path = str(service_dir / "movie_vectorstore")
        elif not os.path.isabs(self._config.faiss_index_path):
            # Resolve relative path relative to service directory
            resolved_faiss_path = str(service_dir / self._config.faiss_index_path)
            self._config.faiss_index_path = resolved_faiss_path
        
        # Build vector store if it doesn't exist
        self._ensure_vector_store()
        
        # Create service instance
        self._service = MovieAgentService(self._config)
        
        # Load movies dataset for statistics tool
        loader = MovieDataLoader(self._config.movies_csv_path)
        movies = loader.load_movies()
        self._service.set_movies(movies)
        
        # Build semantic resolver (for query correction and title inference)
        title_resolver = create_title_resolver(config=self._config)
        
        # Create and inject retriever
        retriever = create_retriever(config=self._config, title_resolver=title_resolver)
        self._service.set_vector_store(retriever)
        
        # Create and inject vision tool if enabled
        if self._config.enable_vision:
            # Vision tool is pure vision (caption generation only)
            # Movie identification is agent's responsibility via movie_search
            vision_tool = create_vision_tool(config=self._config)
            self._service.set_vision_analyst(vision_tool)
        
        # Create and inject LLM
        self._config.llm = get_llm_instance(
            provider=self._config.llm_provider,
            model=self._config.llm_model
        )
        
        # Warmup the service
        self._service.warmup()
    
    def chat(self, query: str, session_id: str = "default") -> ChatResponse:
        """
        Send a chat query to the agent.
        
        :param query: User query string
        :return: ChatResponse with answer, movies, and metadata
        :raises: RuntimeError if initialize() has not been called
        """
        if not self._service:
            raise RuntimeError("App not initialized. Call initialize() first.")
        
        return self._service.chat(query, session_id=session_id)
    
    def analyze_poster(self, image_path: str, session_id: str = "default") -> PosterAnalysisResponse:
        """
        Analyze a movie poster image.
        
        :param image_path: Path to poster image file
        :param session_id: Session identifier for memory storage (defaults to "default")
        :return: PosterAnalysisResponse with inferred genres, mood, and title
        :raises: RuntimeError if initialize() has not been called or vision is disabled
        """
        if not self._service:
            raise RuntimeError("App not initialized. Call initialize() first.")
        
        return self._service.analyze_poster(image_path, session_id=session_id)
    
    def _ensure_vector_store(self) -> None:
        """Build vector store if it doesn't exist."""
        vector_store_path = self._config.faiss_index_path or os.getenv(
            "VECTOR_STORE_PATH", 
            "movie_vectorstore"
        )
        
        if os.path.exists(vector_store_path):
            return
        
        # Build vector store
        from .config_validator import get_required_env, get_optional_env
        embedding_provider = get_optional_env("EMBEDDING_PROVIDER", "openai").lower()
        if embedding_provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            api_key = get_required_env(
                "OPENAI_API_KEY",
                description="OpenAI API key for embeddings (get from https://platform.openai.com/api-keys)"
            )
            embedding_model = OpenAIEmbeddings(openai_api_key=api_key)
        else:
            raise ValueError(f"Unknown embedding provider: {embedding_provider}")
        
        # Load movies and build index
        loader = MovieDataLoader(self._config.movies_csv_path)
        movies = loader.load_movies()
        documents = build_documents(movies)
        
        # Chunk documents
        chunker = MovieChunker()
        chunked_docs = chunker.chunk(documents)
        
        # Build vector store
        vector_store = MovieVectorStore(
            embedding_model=embedding_model,
            index_path=vector_store_path
        )
        vector_store.build(chunked_docs)

