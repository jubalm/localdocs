"""
Security-focused validation utilities for LocalDocs.

This module provides robust validation functions to prevent security vulnerabilities
including SSRF, path traversal, and input validation attacks.
"""

import re
import socket
import urllib.parse
import urllib.request
import urllib.error
from ipaddress import ip_address, ip_network, AddressValueError
from pathlib import Path
from typing import List, Optional, Set, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class SSRFError(ValidationError):
    """Exception raised when SSRF vulnerability is detected."""
    pass


class PathTraversalError(ValidationError):
    """Exception raised when path traversal attempt is detected."""
    pass


# Private IP ranges that should be blocked for SSRF protection
PRIVATE_IP_RANGES = [
    ip_network('10.0.0.0/8'),      # RFC 1918 - Private networks
    ip_network('172.16.0.0/12'),   # RFC 1918 - Private networks  
    ip_network('192.168.0.0/16'),  # RFC 1918 - Private networks
    ip_network('127.0.0.0/8'),     # RFC 3330 - Loopback
    ip_network('169.254.0.0/16'),  # RFC 3927 - Link-local
    ip_network('224.0.0.0/4'),     # RFC 5771 - Multicast
    ip_network('240.0.0.0/4'),     # RFC 1112 - Reserved
    ip_network('::1/128'),         # IPv6 loopback
    ip_network('fc00::/7'),        # IPv6 unique local
    ip_network('fe80::/10'),       # IPv6 link-local
]

# Allowed URL schemes to prevent protocol confusion attacks
ALLOWED_SCHEMES = {'http', 'https'}

# Allowed content types for documentation downloads
ALLOWED_CONTENT_TYPES = {
    'text/plain',
    'text/markdown', 
    'text/html',
    'text/x-markdown',
    'application/octet-stream'  # Some servers don't set proper content types
}

# Reserved Windows filenames that should be blocked
RESERVED_NAMES = {
    'con', 'prn', 'aux', 'nul', 
    'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
    'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
}


def validate_url_security(url: str, timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Validate URL for security vulnerabilities including SSRF.
    
    Args:
        url: The URL to validate
        timeout: Timeout for DNS resolution and connection attempts
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Raises:
        SSRFError: If SSRF vulnerability is detected
        ValidationError: If other validation errors occur
    """
    try:
        # Parse the URL
        parsed = urllib.parse.urlparse(url)
        
        # Validate scheme
        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            raise SSRFError(f"Scheme '{parsed.scheme}' not allowed. Only HTTP/HTTPS are permitted.")
        
        # Validate hostname exists
        if not parsed.hostname:
            raise ValidationError("URL must contain a valid hostname")
        
        # Resolve hostname to IP address
        try:
            host_ip = socket.gethostbyname(parsed.hostname)
            ip_addr = ip_address(host_ip)
        except (socket.gaierror, AddressValueError) as e:
            raise ValidationError(f"Cannot resolve hostname '{parsed.hostname}': {e}")
        
        # Check if IP is in private ranges (SSRF protection)
        for private_range in PRIVATE_IP_RANGES:
            if ip_addr in private_range:
                raise SSRFError(f"Access to private IP address {ip_addr} is not allowed")
        
        # Validate port if specified
        if parsed.port:
            if parsed.port < 1 or parsed.port > 65535:
                raise ValidationError(f"Invalid port number: {parsed.port}")
            # Block common dangerous ports
            dangerous_ports = {22, 23, 25, 53, 110, 143, 993, 995}
            if parsed.port in dangerous_ports:
                raise SSRFError(f"Access to port {parsed.port} is not allowed")
        
        # Attempt connection with timeout to validate URL accessibility
        try:
            request = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (LocalDocs/1.0; Documentation Downloader)'
            })
            
            with urllib.request.urlopen(request, timeout=timeout) as response:
                # Validate content type
                content_type = response.headers.get('content-type', '').lower().split(';')[0]
                if content_type and content_type not in ALLOWED_CONTENT_TYPES:
                    return False, f"Content type '{content_type}' not allowed for documentation"
                
                # Check response size (prevent zip bombs)
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB limit
                    return False, "Content too large (max 50MB allowed)"
                
                return True, None
                
        except urllib.error.HTTPError as e:
            return False, f"HTTP error {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return False, f"URL error: {e.reason}"
        except socket.timeout:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Unexpected error: {e}"
            
    except (SSRFError, ValidationError):
        raise
    except Exception as e:
        raise ValidationError(f"URL validation failed: {e}")


def validate_package_name(package_name: str) -> bool:
    """
    Validate package name for security and filesystem compatibility.
    
    Args:
        package_name: The package name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not package_name or not isinstance(package_name, str):
        return False
    
    # Length check
    if len(package_name) > 255:
        return False
    
    # Check for path traversal attempts
    if '..' in package_name or package_name.startswith('/') or package_name.startswith('\\'):
        return False
    
    # Only allow safe characters: alphanumeric, hyphens, underscores, and dots
    if not re.match(r'^[a-zA-Z0-9._-]+$', package_name):
        return False
    
    # Disallow reserved names (Windows compatibility)
    if package_name.lower() in RESERVED_NAMES:
        return False
    
    # Don't allow names that are just dots or start/end with dots
    if package_name.startswith('.') or package_name.endswith('.') or package_name == '.':
        return False
    
    return True


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to prevent directory traversal and ensure filesystem compatibility.
    
    Args:
        filename: The filename to sanitize
        max_length: Maximum allowed length for the filename
        
    Returns:
        Sanitized filename
        
    Raises:
        PathTraversalError: If path traversal attempt is detected
    """
    if not filename or not isinstance(filename, str):
        raise ValidationError("Filename cannot be empty")
    
    # Check for path traversal attempts before processing
    if '..' in filename or '/' in filename or '\\' in filename:
        raise PathTraversalError("Path traversal detected in filename")
    
    # Remove path components and just keep the filename
    filename = str(Path(filename).name)
    
    # Replace dangerous characters with underscores
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Handle reserved names
    name_part = filename.split('.')[0].lower()
    if name_part in RESERVED_NAMES:
        filename = f"safe_{filename}"
    
    # Limit length while preserving extension
    if len(filename) > max_length:
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            filename = f"{name[:max_name_length]}.{ext}"
        else:
            filename = filename[:max_length]
    
    # Ensure filename is not empty after sanitization
    if not filename or filename == '.':
        filename = "sanitized_file"
    
    return filename


def validate_config_path(config_path: Path) -> Path:
    """
    Validate and secure config path to prevent path traversal.
    
    Args:
        config_path: The config path to validate
        
    Returns:
        Validated and resolved config path
        
    Raises:
        PathTraversalError: If path traversal attempt is detected
        ValidationError: If path is invalid
    """
    if not isinstance(config_path, Path):
        config_path = Path(config_path)
    
    try:
        # Resolve the path to detect any path traversal attempts
        resolved_path = config_path.resolve()
        
        # Ensure the resolved path is within safe boundaries
        # Check if trying to access system directories
        str_path = str(resolved_path).lower()
        dangerous_paths = ['/etc/', '/usr/', '/var/', '/sys/', '/proc/', '/dev/', '/root/']
        if any(str_path.startswith(dp) for dp in dangerous_paths):
            raise PathTraversalError(f"Access to system directory not allowed: {resolved_path}")
        
        # Ensure filename is safe
        if resolved_path.name != "localdocs.config.json":
            raise ValidationError("Config file must be named 'localdocs.config.json'")
        
        return resolved_path
        
    except OSError as e:
        raise ValidationError(f"Invalid path: {e}")


def validate_and_clean_tags(tags_input: str) -> List[str]:
    """
    Validate and clean tag input string.
    
    Args:
        tags_input: Comma-separated tag string
        
    Returns:
        List of valid, cleaned tags
    """
    if not tags_input or not tags_input.strip():
        return []
    
    # Split by comma and clean each tag
    raw_tags = [tag.strip().lower() for tag in tags_input.split(',')]
    valid_tags = []
    
    for tag in raw_tags:
        if not tag:  # Skip empty strings
            continue
        
        # Validate tag format: alphanumeric + hyphens, max 20 chars
        if not re.match(r'^[a-z0-9-]+$', tag) or len(tag) > 20 or len(tag) < 1:
            continue  # Skip invalid tags silently
        
        # Avoid duplicates
        if tag not in valid_tags:
            valid_tags.append(tag)
    
    # Limit to 10 tags max
    return valid_tags[:10]


def validate_document_metadata(name: Optional[str] = None, 
                             description: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate and sanitize document metadata.
    
    Args:
        name: Document name
        description: Document description
        
    Returns:
        Tuple of (sanitized_name, sanitized_description)
    """
    sanitized_name = None
    sanitized_description = None
    
    if name is not None:
        # Strip and limit length
        name = name.strip()
        if len(name) > 200:
            name = name[:200]
        # Remove control characters
        name = re.sub(r'[\x00-\x1f\x7f]', '', name)
        sanitized_name = name if name else None
    
    if description is not None:
        # Strip and limit length
        description = description.strip()
        if len(description) > 1000:
            description = description[:1000]
        # Remove control characters
        description = re.sub(r'[\x00-\x1f\x7f]', '', description)
        sanitized_description = description if description else None
    
    return sanitized_name, sanitized_description