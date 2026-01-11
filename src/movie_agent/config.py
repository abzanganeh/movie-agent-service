from dataclasses import dataclass, field
from typing import Optional, Any, Literal


@dataclass
class MovieAgentConfig:
    # Core Paths
    movies_csv_path: str = "data/movies.csv"
    
    # Vector Store
    faiss_index_path: Optional[str] = None
    faiss_gpu_enabled: bool = field(default=False)  # Enable GPU acceleration for FAISS
    
    # LLM / Agent
    llm_provider: str = 'groq'
    
    llm_model: str = "llama-3.1-8b-instant"
    llm: Any = field(default=None)  # Injected LLM instance
    verbose: bool = field(default=False)  # Verbose output flag
    
    # Hardware Configuration
    device: Optional[Literal["auto", "cpu", "cuda", "mps"]] = field(
        default="auto",
        metadata={
            "description": "Device to use for model inference. 'auto' detects best available (GPU preferred), "
                          "'cpu' forces CPU, 'cuda' uses NVIDIA GPU, 'mps' uses Apple Silicon GPU."
        }
    )
    force_cpu: bool = field(
        default=False,
        metadata={
            "description": "Force CPU usage even if GPU is available (overrides device='auto')"
        }
    )
    log_hardware_info: bool = field(
        default=True,
        metadata={
            "description": "Log hardware detection results on startup"
        }
    )
    
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
    
    