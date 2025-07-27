"""
LocalDocs - Simple documentation downloader optimized for LLM workflows.

This package provides secure and efficient tools for downloading, managing,
and organizing documentation from web sources with focus on security and
user experience.
"""

__version__ = "2.0.0"
__author__ = "LocalDocs Team"
__description__ = "Simple documentation downloader optimized for LLM workflows"

from .exceptions import (
    LocalDocsError,
    ValidationError,
    SSRFError,
    PathTraversalError,
    NetworkError,
    DownloadError,
    ContentTooLargeError
)

__all__ = [
    'LocalDocsError',
    'ValidationError', 
    'SSRFError',
    'PathTraversalError',
    'NetworkError',
    'DownloadError',
    'ContentTooLargeError'
]