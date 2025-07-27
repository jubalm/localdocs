"""
Utility modules for LocalDocs.

This package contains utility functions for validation, configuration,
terminal operations, and network communication.
"""

from .validation import (
    ValidationError,
    SSRFError, 
    PathTraversalError,
    validate_url_security,
    validate_package_name,
    sanitize_filename,
    validate_config_path,
    validate_and_clean_tags,
    validate_document_metadata
)

from .config import (
    DocumentMetadata,
    ConfigManager,
    create_config_manager
)

from .terminal import (
    get_char,
    clear_screen,
    is_interactive_capable,
    get_terminal_size,
    build_centered_line,
    render_controls,
    wrap_text,
    truncate_text,
    calculate_column_widths,
    TerminalResizeDetector
)

from .network_simple import (
    NetworkError,
    DownloadError,
    ContentTooLargeError,
    validate_url_async,
    validate_url_sync,
    download_content_async,
    download_content_sync
)

__all__ = [
    # Validation
    'ValidationError',
    'SSRFError',
    'PathTraversalError',
    'validate_url_security',
    'validate_package_name',
    'sanitize_filename', 
    'validate_config_path',
    'validate_and_clean_tags',
    'validate_document_metadata',
    
    # Configuration
    'DocumentMetadata',
    'ConfigManager',
    'create_config_manager',
    
    # Terminal
    'get_char',
    'clear_screen',
    'is_interactive_capable',
    'get_terminal_size',
    'build_centered_line',
    'render_controls',
    'wrap_text',
    'truncate_text',
    'calculate_column_widths',
    'TerminalResizeDetector',
    
    # Network
    'NetworkError',
    'DownloadError',
    'ContentTooLargeError',
    'validate_url_async',
    'validate_url_sync',
    'download_content_async',
    'download_content_sync'
]