"""
Custom exceptions for the Alfred Snippets Automation system.
"""


class SnippetError(Exception):
    """Base exception for all snippet-related errors."""
    pass


class AlfredFolderError(SnippetError):
    """Raised when there are issues with Alfred folder operations."""
    pass


class APIError(SnippetError):
    """Raised when there are issues with API calls."""
    pass


class DuplicateSnippetError(SnippetError):
    """Raised when attempting to create a duplicate snippet."""
    pass


class ValidationError(SnippetError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(SnippetError):
    """Raised when there are configuration issues."""
    pass


class NetworkError(APIError):
    """Raised when there are network connectivity issues."""
    pass


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""
    pass