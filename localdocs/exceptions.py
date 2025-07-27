"""
Custom exceptions for LocalDocs.

This module defines all custom exceptions used throughout the LocalDocs
application with proper inheritance hierarchy and error messages.
"""


class LocalDocsError(Exception):
    """Base exception for all LocalDocs errors."""
    
    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ValidationError(LocalDocsError):
    """Exception raised when input validation fails."""
    pass


class SSRFError(ValidationError):
    """Exception raised when SSRF vulnerability is detected."""
    pass


class PathTraversalError(ValidationError):
    """Exception raised when path traversal attempt is detected."""
    pass


class NetworkError(LocalDocsError):
    """Base exception for network-related errors."""
    pass


class DownloadError(NetworkError):
    """Exception raised when download operation fails."""
    pass


class ContentTooLargeError(NetworkError):
    """Exception raised when content exceeds size limits."""
    pass


class ConfigurationError(LocalDocsError):
    """Exception raised when configuration is invalid or cannot be loaded."""
    pass


class DocumentNotFoundError(LocalDocsError):
    """Exception raised when requested document is not found."""
    pass


class PackagingError(LocalDocsError):
    """Exception raised when document packaging fails."""
    pass


class InteractiveError(LocalDocsError):
    """Exception raised during interactive mode operations."""
    pass