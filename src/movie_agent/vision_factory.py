# src/movie_agent/vision_factory.py
import os
from typing import Optional
from .tools.blip_vision_tool import BLIPVisionTool
from .config import MovieAgentConfig


def create_vision_tool(
    config: Optional[MovieAgentConfig] = None,
) -> BLIPVisionTool:
    """
    Factory function to create a configured BLIPVisionTool instance.
    
    Follows Single Responsibility Principle:
    - Vision tool ONLY generates captions (evidence)
    - Movie identification is agent's responsibility (via movie_search)
    
    :param config: MovieAgentConfig instance (optional, uses defaults if not provided)
    :return: Configured BLIPVisionTool instance (pure vision, no retrieval)
    """
    if config is None:
        # Use defaults from config
        model_name = os.getenv("VISION_MODEL_NAME", "Salesforce/blip-image-captioning-base")
        model_path = os.getenv("VISION_MODEL_PATH", None)
    else:
        model_name = config.vision_model_name
        model_path = config.vision_model_path
    
    return BLIPVisionTool(
        model_name=model_name,
        model_path=model_path,
    )