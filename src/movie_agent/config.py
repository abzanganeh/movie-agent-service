from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class MovieAgentConfig:
    # Core Paths
    movies_csv_path: str = "data/movies.csv"
    
    # Vector Store
    faiss_index_path: Optional[str] = None
    
    # LLM / Agent
    llm_provider: str = 'groq'
    
    llm_model: str = "llama-3.1-8b-instant"
    llm: Any = field(default=None)  # Injected LLM instance
    verbose: bool = field(default=False)  # Verbose output flag
    
    # Vision
    enable_vision: bool = False
    vision_model_name: str = field(default="Salesforce/blip-image-captioning-base")  # BLIP model name/path
    vision_model_path: Optional[str] = field(default=None)  # Optional local model path
    
    # Performance
    warmup_on_start: bool = True
    
    # Semantic Resolution (Fuzzy Matching)
    enable_fuzzy_matching: bool = True
    fuzzy_threshold: float = field(default=0.75)  # Minimum score for fuzzy matches (0.0-1.0)
    resolution_confidence_threshold: float = field(default=0.75)  # Minimum confidence to accept resolution
    
    # Memory
    enable_memory: bool = field(default=False)  # Feature flag - memory off by default
    memory_max_turns: int = field(default=10)  # Maximum conversation turns to remember
    
    