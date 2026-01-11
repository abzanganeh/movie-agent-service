"""
Configuration validation utilities.

Senior-level configuration management with proper validation and error handling.
"""
import os
from typing import Optional
from .exceptions import ConfigurationError


def get_required_env(key: str, description: str = None) -> str:
    """
    Get required environment variable with validation.
    
    :param key: Environment variable name
    :param description: Human-readable description for error messages
    :return: Environment variable value
    :raises: ConfigurationError if not set or invalid
    """
    value = os.getenv(key)
    
    if not value:
        desc = description or key
        raise ConfigurationError(
            f"{key} is required but not set.\n"
            f"Please set it using one of these methods:\n"
            f"  1. Environment variable: export {key}='your-value'\n"
            f"  2. .env file: Create .env in project root with {key}=your-value\n"
            f"  3. See .env.example for template\n\n"
            f"Description: {desc}"
        )
    
    # Validate it's not a placeholder
    if _is_placeholder(value):
        raise ConfigurationError(
            f"{key} appears to be a placeholder value.\n"
            f"Please set a real value. Current value: {_mask_secret(value)}\n"
            f"See .env.example for the correct format."
        )
    
    return value


def get_optional_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get optional environment variable.
    
    :param key: Environment variable name
    :param default: Default value if not set
    :return: Environment variable value or default
    """
    value = os.getenv(key, default)
    
    if value and _is_placeholder(value):
        # Warn but don't fail for optional configs
        import warnings
        warnings.warn(
            f"{key} appears to be a placeholder. Using default or None.",
            UserWarning
        )
        return default
    
    return value


def validate_api_key(key: str, key_name: str, min_length: int = 20) -> str:
    """
    Validate API key format.
    
    :param key: API key to validate
    :param key_name: Name of the key (for error messages)
    :param min_length: Minimum expected length
    :return: Validated key
    :raises: ConfigurationError if invalid
    """
    if not key:
        raise ConfigurationError(f"{key_name} is required.")
    
    if _is_placeholder(key):
        raise ConfigurationError(
            f"{key_name} appears to be a placeholder. "
            f"Please set a real API key."
        )
    
    if len(key) < min_length:
        raise ConfigurationError(
            f"{key_name} appears to be invalid (too short: {len(key)} chars). "
            f"Expected at least {min_length} characters."
        )
    
    return key


def _is_placeholder(value: str) -> bool:
    """Check if value is a placeholder."""
    if not value:
        return False
    
    placeholder_patterns = [
        "your_",
        "placeholder",
        "example",
        "xxx",
        "sk-0000",
        "gsk_0000",
        "replace",
        "TODO",
    ]
    
    value_lower = value.lower()
    return any(pattern in value_lower for pattern in placeholder_patterns)


def _mask_secret(secret: str, show_chars: int = 4) -> str:
    """
    Mask secret for safe display in error messages.
    
    :param secret: Secret to mask
    :param show_chars: Number of characters to show at start/end
    :return: Masked secret
    """
    if not secret or len(secret) <= show_chars * 2:
        return "***"
    
    return f"{secret[:show_chars]}...{secret[-show_chars:]}"


def validate_path(path: str, path_name: str, must_exist: bool = False) -> str:
    """
    Validate file/directory path.
    
    :param path: Path to validate
    :param path_name: Name of the path (for error messages)
    :param must_exist: Whether path must exist
    :return: Validated path
    :raises: ConfigurationError if invalid
    """
    if not path:
        raise ConfigurationError(f"{path_name} is required.")
    
    if must_exist and not os.path.exists(path):
        raise ConfigurationError(
            f"{path_name} does not exist: {path}\n"
            f"Please check the path and ensure the file/directory exists."
        )
    
    return path

