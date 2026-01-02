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
    llm_model: str = 'llama-3.1-8b'
    llm: Any = field(default=None)  # Injected LLM instance
    verbose: bool = field(default=False)  # Verbose output flag
    
    # Vision
    enable_vision: bool = False
    
    # Performance
    warmup_on_start: bool = True
    
    