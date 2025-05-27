"""
Alfred Snippets Automation

An intelligent automation system for creating and managing Alfred snippets
using Anthropic's Claude API for metadata generation and categorization.
"""

__version__ = "0.1.0"
__author__ = "Shayon Pal"
__email__ = "shayon@example.com"

from .snippet_manager import SnippetManager
from .claude_api import ClaudeAPI
from .alfred_utils import AlfredUtils
from .exceptions import (
    SnippetError,
    AlfredFolderError,
    APIError,
    DuplicateSnippetError,
    ValidationError
)

__all__ = [
    "SnippetManager",
    "ClaudeAPI", 
    "AlfredUtils",
    "SnippetError",
    "AlfredFolderError",
    "APIError",
    "DuplicateSnippetError",
    "ValidationError"
]