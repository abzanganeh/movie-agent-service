from typing import List, Optional
import logging
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)


class MovieVectorStore:
    """
    Storage layer for FAISS vector index.
    
    Single Responsibility: Build, load, and save vector indexes.
    Does NOT handle retrieval - that's a separate concern.
    
    Note: GPU acceleration for FAISS requires faiss-gpu package.
    CPU-based FAISS (faiss-cpu) is used by default.
    """
    
    def __init__(self, embedding_model, index_path: str, use_gpu: bool = False):
        """
        Initialize vector store.
        
        :param embedding_model: Embedding model for vectorization
        :param index_path: Path to store/load FAISS index
        :param use_gpu: Whether to attempt GPU acceleration (requires faiss-gpu)
        """
        self._embedding_model = embedding_model
        self._index_path = index_path
        self._use_gpu = use_gpu
        self._vectorstore: FAISS | None = None
        self._gpu_resources = None
        
        if use_gpu:
            self._setup_gpu_if_available()
    
    def _setup_gpu_if_available(self) -> None:
        """
        Set up GPU resources for FAISS if available.
        
        Note: Requires faiss-gpu package and CUDA-compatible GPU.
        Falls back to CPU silently if GPU is not available.
        """
        try:
            import faiss
            if hasattr(faiss, 'StandardGpuResources'):
                # FAISS GPU is available
                try:
                    self._gpu_resources = faiss.StandardGpuResources()
                    logger.info("FAISS GPU resources initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize FAISS GPU resources: {e}. Falling back to CPU.")
                    self._use_gpu = False
            else:
                logger.warning("FAISS GPU not available (faiss-gpu package required). Using CPU.")
                self._use_gpu = False
        except ImportError:
            logger.warning("faiss-gpu package not found. Install with: pip install faiss-gpu. Using CPU.")
            self._use_gpu = False
        except Exception as e:
            logger.warning(f"Error checking FAISS GPU availability: {e}. Using CPU.")
            self._use_gpu = False
    
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