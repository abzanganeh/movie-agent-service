"""
Input validation and sanitization.

OOP: Single Responsibility - Only handles input validation and sanitization.
"""

import re
import html
from typing import Optional

from .exceptions import ValidationError


class InputValidator:
    """
    Validates and sanitizes user input.
    
    Prevents prompt injection and validates input length/content.
    """

    MAX_QUERY_LENGTH = 500
    MAX_TOOL_PARAM_LENGTH = 1000

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above|all)\s+instructions?",
        r"(system|assistant|prompt)\s*:",
        r"you\s+are\s+(now|a|an)",
        r"forget\s+everything",
        r"disregard\s+(the\s+)?(above|previous)",
        r"override\s+(previous|above|all)",
        r"act\s+as\s+(if|though)",
        r"pretend\s+to\s+be",
    ]

    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        Sanitize user query to prevent prompt injection.
        
        :param query: User's query string
        :return: Sanitized query string
        :raises ValidationError: If query is invalid or contains malicious content
        """
        if not query or not isinstance(query, str):
            raise ValidationError("Query must be a non-empty string")

        if len(query) > InputValidator.MAX_QUERY_LENGTH:
            raise ValidationError(
                f"Query exceeds maximum length of {InputValidator.MAX_QUERY_LENGTH} characters"
            )

        query_lower = query.lower()

        for pattern in InputValidator.INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                raise ValidationError(
                    "Query contains potentially malicious content. Please rephrase your question."
                )

        sanitized = html.escape(query)
        sanitized = sanitized.replace("\x00", "")
        sanitized = sanitized.strip()

        if not sanitized:
            raise ValidationError("Query cannot be empty after sanitization")

        return sanitized

    @staticmethod
    def validate_tool_parameters(tool_name: str, params: dict) -> dict:
        """
        Validate and sanitize tool parameters.
        
        :param tool_name: Name of the tool
        :param params: Tool parameters dictionary
        :return: Validated parameters dictionary
        :raises ValidationError: If parameters are invalid
        """
        if not isinstance(params, dict):
            raise ValidationError("Parameters must be a dictionary")

        validated = {}

        for key, value in params.items():
            if not isinstance(key, str):
                raise ValidationError(f"Parameter key must be string, got {type(key)}")

            if isinstance(value, str):
                if len(value) > InputValidator.MAX_TOOL_PARAM_LENGTH:
                    raise ValidationError(
                        f"Parameter '{key}' exceeds maximum length of "
                        f"{InputValidator.MAX_TOOL_PARAM_LENGTH} characters"
                    )
                value = html.escape(value)
                value = value.replace("\x00", "")

            validated[key] = value

        return validated

    @staticmethod
    def validate_length(text: str, max_length: int, field_name: str = "Input") -> str:
        """
        Validate text length.
        
        :param text: Text to validate
        :param max_length: Maximum allowed length
        :param field_name: Name of the field for error messages
        :return: Validated text
        :raises ValidationError: If text exceeds maximum length
        """
        if not isinstance(text, str):
            raise ValidationError(f"{field_name} must be a string")

        if len(text) > max_length:
            raise ValidationError(
                f"{field_name} exceeds maximum length of {max_length} characters"
            )

        return text

