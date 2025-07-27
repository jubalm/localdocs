"""
Network utilities for LocalDocs with security and performance optimizations.

This module provides secure HTTP operations with SSRF protection,
async/await support, streaming downloads, and proper error handling.
"""

import asyncio
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator
import time

# Optional aiohttp import for async operations
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

from .validation import validate_url_security, SSRFError, ValidationError


# Network operation timeouts
DEFAULT_TIMEOUT = 30
VALIDATION_TIMEOUT = 10
DOWNLOAD_TIMEOUT = 60
CHUNK_SIZE = 8192  # 8KB chunks for streaming

# Size limits
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
MAX_REDIRECTS = 5

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


async def validate_url_async(url: str, timeout: int = VALIDATION_TIMEOUT) -> bool:
    """
    Asynchronously validate URL accessibility with security checks.
    
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
    if not AIOHTTP_AVAILABLE:
        raise NetworkError("aiohttp not available for async operations")
    
    # First perform security validation
    try:
        is_valid, error_msg = validate_url_security(url, timeout)
        if not is_valid:
            raise NetworkError(error_msg or "URL validation failed")
        return True
    except (SSRFError, ValidationError):
        raise
    except Exception as e:
        raise NetworkError(f"URL validation error: {e}")


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


async def download_content_async(url: str, 
                                max_size: int = MAX_CONTENT_LENGTH,
                                timeout: int = DOWNLOAD_TIMEOUT) -> str:
    """
    Asynchronously download content from URL with security checks.
    
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
    await validate_url_async(url, VALIDATION_TIMEOUT)
    
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    headers = {'User-Agent': USER_AGENT}
    
    try:
        async with aiohttp.ClientSession(
            timeout=timeout_config,
            headers=headers,
            max_redirects=MAX_REDIRECTS
        ) as session:
            async with session.get(url) as response:
                # Check response status
                if response.status >= 400:
                    raise DownloadError(f"HTTP {response.status}: {response.reason}")
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > max_size:
                    raise ContentTooLargeError(f"Content too large: {content_length} bytes")
                
                # Download content with size checking
                content_chunks = []
                total_size = 0
                
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
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
                    
    except aiohttp.ClientError as e:
        raise NetworkError(f"Network error: {e}")
    except asyncio.TimeoutError:
        raise NetworkError("Download timeout")
    except (SSRFError, ValidationError, ContentTooLargeError, DownloadError):
        raise
    except Exception as e:
        raise DownloadError(f"Unexpected download error: {e}")


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


async def stream_download_to_file(url: str, 
                                 file_path: Path,
                                 max_size: int = MAX_CONTENT_LENGTH,
                                 timeout: int = DOWNLOAD_TIMEOUT) -> int:
    """
    Stream download content directly to file for large files.
    
    Args:
        url: URL to download from
        file_path: Path where to save the content
        max_size: Maximum allowed content size in bytes
        timeout: Timeout for download operation
        
    Returns:
        Number of bytes downloaded
        
    Raises:
        SSRFError: If SSRF vulnerability detected
        ValidationError: If validation fails
        NetworkError: If network error occurs
        ContentTooLargeError: If content exceeds size limit
        DownloadError: If download fails
    """
    # Validate URL security first
    await validate_url_async(url, VALIDATION_TIMEOUT)
    
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    headers = {'User-Agent': USER_AGENT}
    
    try:
        async with aiohttp.ClientSession(
            timeout=timeout_config,
            headers=headers,
            max_redirects=MAX_REDIRECTS
        ) as session:
            async with session.get(url) as response:
                # Check response status
                if response.status >= 400:
                    raise DownloadError(f"HTTP {response.status}: {response.reason}")
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > max_size:
                    raise ContentTooLargeError(f"Content too large: {content_length} bytes")
                
                # Stream to file
                total_size = 0
                
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                        total_size += len(chunk)
                        if total_size > max_size:
                            file_path.unlink(missing_ok=True)  # Clean up partial file
                            raise ContentTooLargeError(f"Content exceeded {max_size} bytes")
                        
                        f.write(chunk)
                
                return total_size
                
    except aiohttp.ClientError as e:
        file_path.unlink(missing_ok=True)  # Clean up on error
        raise NetworkError(f"Network error: {e}")
    except asyncio.TimeoutError:
        file_path.unlink(missing_ok=True)  # Clean up on timeout
        raise NetworkError("Download timeout")
    except (SSRFError, ValidationError, ContentTooLargeError, DownloadError):
        file_path.unlink(missing_ok=True)  # Clean up on error
        raise
    except Exception as e:
        file_path.unlink(missing_ok=True)  # Clean up on error
        raise DownloadError(f"Unexpected download error: {e}")


class DownloadProgress:
    """Track download progress for user feedback."""
    
    def __init__(self, url: str):
        self.url = url
        self.start_time = time.time()
        self.bytes_downloaded = 0
        self.total_bytes: Optional[int] = None
        self.completed = False
        self.error: Optional[str] = None
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    @property
    def download_speed(self) -> float:
        """Get download speed in bytes per second."""
        if self.elapsed_time == 0:
            return 0.0
        return self.bytes_downloaded / self.elapsed_time
    
    @property
    def progress_percentage(self) -> Optional[float]:
        """Get progress percentage if total size is known."""
        if self.total_bytes and self.total_bytes > 0:
            return (self.bytes_downloaded / self.total_bytes) * 100.0
        return None
    
    def update(self, bytes_downloaded: int, total_bytes: Optional[int] = None) -> None:
        """Update progress information."""
        self.bytes_downloaded = bytes_downloaded
        if total_bytes is not None:
            self.total_bytes = total_bytes
    
    def mark_completed(self) -> None:
        """Mark download as completed."""
        self.completed = True
    
    def mark_error(self, error: str) -> None:
        """Mark download as failed with error."""
        self.error = error
        self.completed = True


async def download_with_progress(url: str, 
                               progress_callback: Optional[callable] = None,
                               max_size: int = MAX_CONTENT_LENGTH,
                               timeout: int = DOWNLOAD_TIMEOUT) -> str:
    """
    Download content with progress tracking.
    
    Args:
        url: URL to download from
        progress_callback: Optional callback function to receive progress updates
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
    progress = DownloadProgress(url)
    
    try:
        # Validate URL security first
        await validate_url_async(url, VALIDATION_TIMEOUT)
        
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        headers = {'User-Agent': USER_AGENT}
        
        async with aiohttp.ClientSession(
            timeout=timeout_config,
            headers=headers,
            max_redirects=MAX_REDIRECTS
        ) as session:
            async with session.get(url) as response:
                # Check response status
                if response.status >= 400:
                    raise DownloadError(f"HTTP {response.status}: {response.reason}")
                
                # Get content length
                content_length = response.headers.get('content-length')
                total_bytes = int(content_length) if content_length else None
                
                if total_bytes and total_bytes > max_size:
                    raise ContentTooLargeError(f"Content too large: {total_bytes} bytes")
                
                progress.update(0, total_bytes)
                if progress_callback:
                    progress_callback(progress)
                
                # Download content with progress updates
                content_chunks = []
                total_size = 0
                
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                    total_size += len(chunk)
                    if total_size > max_size:
                        raise ContentTooLargeError(f"Content exceeded {max_size} bytes")
                    
                    content_chunks.append(chunk)
                    progress.update(total_size, total_bytes)
                    
                    if progress_callback:
                        progress_callback(progress)
                
                # Decode content
                content_bytes = b''.join(content_chunks)
                try:
                    content = content_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    # Try other encodings
                    for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            content = content_bytes.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        raise DownloadError("Cannot decode content")
                
                progress.mark_completed()
                if progress_callback:
                    progress_callback(progress)
                
                return content
                
    except Exception as e:
        error_msg = str(e)
        progress.mark_error(error_msg)
        if progress_callback:
            progress_callback(progress)
        raise