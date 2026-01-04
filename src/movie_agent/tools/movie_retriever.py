from typing import List, Optional
from langchain_core.documents import Document
from .retriever_tool import RetrieverTool  # protocol
from ..vector_store import MovieVectorStore
from ..resolution import MovieTitleResolver, EntityExtractor, ResolutionMetadata


class MovieRetriever(RetrieverTool):
    """
    Retrieval layer for movie search.
    
    Single Responsibility: Retrieve documents matching queries.
    Implements RetrieverTool protocol directly.
    
    Uses MovieVectorStore for storage (composition, not inheritance).
    """
    
    def __init__(
        self,
        vector_store: MovieVectorStore,
        k: int = 5,
        title_resolver: Optional[MovieTitleResolver] = None,
        enable_entity_extraction: bool = True,
    ):
        """
        :param vector_store: MovieVectorStore instance (must be initialized)
        :param k: Default number of results to return
        :param title_resolver: Optional MovieTitleResolver for query correction and entity normalization
        :param enable_entity_extraction: Whether to extract entities before resolution (default: True)
        """
        if not vector_store.is_initialized():
            raise RuntimeError(
                "MovieVectorStore must be initialized (call build() or load()) "
                "before creating MovieRetriever"
            )
        self._vector_store = vector_store
        self._default_k = k
        self._title_resolver = title_resolver
        self._entity_extractor = EntityExtractor() if enable_entity_extraction else None
        self._last_resolution_metadata: Optional[ResolutionMetadata] = None

    def retrieve(self, query: str, k: int = None) -> List[Document]:
        """
        Retrieve top-k movies matching the query.
        
        If title_resolver is provided, applies semantic resolution to correct
        typos and normalize entities before retrieval.
        
        Implements RetrieverTool protocol.
        """
        k = k or self._default_k
        
        # Apply semantic resolution if resolver is available
        resolved_query, resolution_metadata = self._resolve_query(query)
        
        # Store resolution metadata for later access
        self._last_resolution_metadata = resolution_metadata
        
        # Use MovieVectorStore's underlying LangChain FAISS
        langchain_vectorstore = self._vector_store.get_langchain_vectorstore()
        langchain_retriever = langchain_vectorstore.as_retriever(
            search_kwargs={"k": k}
        )
        
        # LangChain deprecates get_relevant_documents; invoke is the current API.
        return langchain_retriever.invoke(resolved_query)
    
    def get_last_resolution_metadata(self) -> Optional[ResolutionMetadata]:
        """Get resolution metadata from the last retrieve() call."""
        return self._last_resolution_metadata
    
    def _resolve_query(self, query: str) -> tuple[str, ResolutionMetadata]:
        """
        Apply semantic resolution to query if resolver is available.
        
        Extracts potential movie titles from query and resolves them.
        Returns corrected query with canonical entities and resolution metadata.
        
        :param query: Original query
        :return: Tuple of (resolved_query, resolution_metadata)
        """
        if not self._title_resolver:
            return query, ResolutionMetadata(
                original_query=query,
                resolved_query=query,
            )
        
        # Strategy: Extract entities first, then resolve each
        if self._entity_extractor:
            return self._resolve_with_entity_extraction(query)
        else:
            return self._resolve_full_query(query)
    
    def _resolve_with_entity_extraction(self, query: str) -> tuple[str, ResolutionMetadata]:
        """
        Extract entities from query, resolve each, then rebuild query.
        
        Example:
        "Find Inceptoin movies" → extract("Inceptoin") → resolve("Inceptoin") → "Find Inception movies"
        """
        entities = self._entity_extractor.extract(query)
        entities_resolved = []
        resolved_query = query
        resolution_strategy = None
        resolution_confidence = None
        
        # Resolve each extracted entity (in reverse order to preserve positions)
        for entity in reversed(entities):
            result = self._title_resolver.resolve(entity.text)
            
            if result.is_confident():
                # Replace entity in query
                resolved_query = (
                    resolved_query[:entity.start_pos] +
                    result.canonical_value +
                    resolved_query[entity.end_pos:]
                )
                
                entities_resolved.append({
                    "original": entity.text,
                    "resolved": result.canonical_value,
                    "strategy": result.strategy_used,
                    "confidence": result.confidence,
                })
                
                # Track overall resolution metadata
                if resolution_strategy is None:
                    resolution_strategy = result.strategy_used
                if resolution_confidence is None or result.confidence < resolution_confidence:
                    resolution_confidence = result.confidence
        
        metadata = ResolutionMetadata(
            original_query=query,
            resolved_query=resolved_query,
            resolution_strategy=resolution_strategy,
            resolution_confidence=resolution_confidence,
            entities_resolved=entities_resolved,
        )
        
        return resolved_query, metadata
    
    def _resolve_full_query(self, query: str) -> tuple[str, ResolutionMetadata]:
        """
        Resolve entire query as a single entity (fallback if extraction disabled).
        """
        result = self._title_resolver.resolve(query)
        
        if result.is_confident():
            metadata = ResolutionMetadata(
                original_query=query,
                resolved_query=result.canonical_value,
                resolution_strategy=result.strategy_used,
                resolution_confidence=result.confidence,
                entities_resolved=[{
                    "original": query,
                    "resolved": result.canonical_value,
                    "strategy": result.strategy_used,
                    "confidence": result.confidence,
                }],
            )
            return result.canonical_value, metadata
        
        # No resolution
        metadata = ResolutionMetadata(
            original_query=query,
            resolved_query=query,
        )
        return query, metadata