from dataclassed import dataclass
from typing import Optional


@dataclass
class MovieAgentConfig:
    # Coere Paths
    movies_csv_path: str
    
    # Vector Store
    faiss_index_path: Optional[str] = None
    
    # LLM / Agent
    llm_prvider: str = 'groq'
    llm_model: str = 'llama-3.1-8b'
    
    
    # Vision
    enable_vision: bool = False
    
    # Performance
    warmup_on_start: bool = True
    
    