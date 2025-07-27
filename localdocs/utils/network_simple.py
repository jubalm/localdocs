"""
Simplified network utilities for LocalDocs without async dependencies.

This module provides secure HTTP operations with SSRF protection
and proper error handling using only standard library components.
"""

import urllib.request
import urllib.error
import socket
from typing import Optional

from .validation import validate_url_security, SSRFError, ValidationError


# Network operation timeouts
DEFAULT_TIMEOUT = 30
VALIDATION_TIMEOUT = 10
DOWNLOAD_TIMEOUT = 60
CHUNK_SIZE = 8192  # 8KB chunks

# Size limits
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

# User agent for requests
USER_AGENT = 'Mozilla/5.0 (LocalDocs/1.0; Documentation Downloader)'


class NetworkError(Exception):
    """Base exception for network operations."""
    pass


class DownloadError(NetworkError):
    """Exception raised when download fails."""
    pass


class ContentTooLargeError(NetworkError):
    """Exception raised when content exceeds size limits."""
    pass


def validate_url_sync(url: str, timeout: int = VALIDATION_TIMEOUT) -> bool:
    """
    Synchronously validate URL accessibility with security checks.
    
    Args:
        url: URL to validate
        timeout: Timeout for validation request
        
    Returns:
        True if URL is valid and accessible
        
    Raises:
        SSRFError: If SSRF vulnerability detected
        ValidationError: If validation fails
        NetworkError: If network error occurs
    """
    try:
        is_valid, error_msg = validate_url_security(url, timeout)
        if not is_valid:
            raise NetworkError(error_msg or "URL validation failed")
        return True
    except (SSRFError, ValidationError):
        raise
    except Exception as e:
        raise NetworkError(f"URL validation error: {e}")


def download_content_sync(url: str, 
                         max_size: int = MAX_CONTENT_LENGTH,
                         timeout: int = DOWNLOAD_TIMEOUT) -> str:
    """
    Synchronously download content from URL with security checks.
    
    Args:
        url: URL to download from
        max_size: Maximum allowed content size in bytes
        timeout: Timeout for download operation
        
    Returns:
        Downloaded content as string
        
    Raises:
        SSRFError: If SSRF vulnerability detected
        ValidationError: If validation fails
        NetworkError: If network error occurs
        ContentTooLargeError: If content exceeds size limit
        DownloadError: If download fails
    """
    # Validate URL security first
    validate_url_sync(url, VALIDATION_TIMEOUT)
    
    try:
        request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > max_size:
                raise ContentTooLargeError(f"Content too large: {content_length} bytes")
            
            # Download with size checking
            content_chunks = []
            total_size = 0
            
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                total_size += len(chunk)
                if total_size > max_size:
                    raise ContentTooLargeError(f"Content exceeded {max_size} bytes during download")
                
                content_chunks.append(chunk)
            
            # Decode content
            content_bytes = b''.join(content_chunks)
            try:
                return content_bytes.decode('utf-8')
            except UnicodeDecodeError as e:
                # Try other common encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        return content_bytes.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                raise DownloadError(f"Cannot decode content: {e}")
                
    except urllib.error.HTTPError as e:
        raise DownloadError(f"HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise NetworkError(f"URL error: {e.reason}")
    except (SSRFError, ValidationError, ContentTooLargeError):
        raise
    except Exception as e:
        raise DownloadError(f"Unexpected download error: {e}")


# Placeholder async functions that fall back to sync
async def validate_url_async(url: str, timeout: int = VALIDATION_TIMEOUT) -> bool:
    """Async wrapper around sync validation (fallback implementation)."""
    return validate_url_sync(url, timeout)


async def download_content_async(url: str, 
                                max_size: int = MAX_CONTENT_LENGTH,
                                timeout: int = DOWNLOAD_TIMEOUT) -> str:
    """Async wrapper around sync download (fallback implementation)."""
    return download_content_sync(url, max_size, timeout)