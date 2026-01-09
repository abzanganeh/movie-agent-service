"""
Security-related exceptions.

OOP: Single Responsibility - Exception classes are separated by concern.
"""


class SecurityError(Exception):
    """Base exception for security violations."""

    pass


class ValidationError(SecurityError):
    """Raised when input validation fails."""

    pass


class ToolPolicyViolationError(SecurityError):
    """Raised when a tool call violates security policy."""

    pass


class FileValidationError(SecurityError):
    """Raised when file validation fails."""

    pass

