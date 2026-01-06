"""
Configuration loader with validation.

Senior-level configuration management following best practices.
"""
import os
from typing import Optional
from dotenv import load_dotenv
from .config import MovieAgentConfig
from .config_validator import get_required_env, get_optional_env, validate_path
from .exceptions import ConfigurationError


def load_config_from_env() -> MovieAgentConfig:
    """
    Load configuration from environment variables with validation.
    
    This is the recommended way to create MovieAgentConfig.
    It validates all required values and provides helpful error messages.
    
    Usage:
        config = load_config_from_env()
        app = MovieAgentApp(config)
        app.initialize()
    
    :return: Validated MovieAgentConfig instance
    :raises: ConfigurationError if required configs are missing or invalid
    """
    # Load .env file if it exists (for local development)
    load_dotenv()
    
    # Build config from environment variables
    config = MovieAgentConfig(
        movies_csv_path=get_optional_env(
            "MOVIE_DATA_CSV_PATH",
            default="data/movies.csv"
        ),
        faiss_index_path=get_optional_env("VECTOR_STORE_PATH"),
        llm_provider=get_optional_env("LLM_PROVIDER", default="groq"),
        llm_model=get_optional_env("LLM_MODEL", default="llama-3.1-8b-instant"),
        verbose=get_optional_env("VERBOSE", "false").lower() == "true",
        enable_vision=get_optional_env("ENABLE_VISION", "false").lower() == "true",
        vision_model_name=get_optional_env(
            "VISION_MODEL_NAME",
            default="Salesforce/blip-image-captioning-base"
        ),
        vision_model_path=get_optional_env("VISION_MODEL_PATH"),
        warmup_on_start=get_optional_env("WARMUP_ON_START", "true").lower() == "true",
        enable_fuzzy_matching=get_optional_env("ENABLE_FUZZY_MATCHING", "true").lower() == "true",
        fuzzy_threshold=float(get_optional_env("FUZZY_THRESHOLD", "0.75")),
        resolution_confidence_threshold=float(
            get_optional_env("RESOLUTION_CONFIDENCE_THRESHOLD", "0.75")
        ),
        enable_memory=get_optional_env("ENABLE_MEMORY", "true").lower() == "true",
        memory_max_turns=int(get_optional_env("MEMORY_MAX_TURNS", "10")),
    )
    
    # Validate paths if they're set
    if config.movies_csv_path:
        validate_path(
            config.movies_csv_path,
            "MOVIE_DATA_CSV_PATH",
            must_exist=True
        )
    
    return config


def create_config_for_production() -> MovieAgentConfig:
    """
    Create configuration for production deployment.
    
    Assumes all required environment variables are set by the deployment platform.
    No .env file loading (environment variables only).
    
    Usage:
        config = create_config_for_production()
        app = MovieAgentApp(config)
        app.initialize()
    
    :return: Validated MovieAgentConfig instance
    :raises: ConfigurationError if required configs are missing
    """
    # Don't load .env in production (use environment variables only)
    # load_dotenv() is intentionally NOT called here
    
    return load_config_from_env()

