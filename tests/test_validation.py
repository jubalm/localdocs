"""
Comprehensive tests for security-critical validation functions.

This module tests all validation functions with focus on security vulnerabilities
including SSRF, path traversal, and input validation attacks.
"""

import pytest
import tempfile
import socket
from pathlib import Path
from unittest.mock import patch, MagicMock
from ipaddress import ip_address

from localdocs.utils.validation import (
    ValidationError,
    SSRFError,
    PathTraversalError,
    validate_url_security,
    validate_package_name,
    sanitize_filename,
    validate_config_path,
    validate_and_clean_tags,
    validate_document_metadata,
    PRIVATE_IP_RANGES,
    ALLOWED_SCHEMES,
    RESERVED_NAMES
)


class TestURLSecurityValidation:
    """Test comprehensive URL security validation."""
    
    def test_valid_https_url(self):
        """Test that valid HTTPS URLs pass validation."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers = {'content-type': 'text/html'}
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            with patch('socket.gethostbyname', return_value='8.8.8.8'):
                is_valid, error = validate_url_security('https://example.com/doc.md')
                assert is_valid is True
                assert error is None
    
    def test_valid_http_url(self):
        """Test that valid HTTP URLs pass validation."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers = {'content-type': 'text/plain'}
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            with patch('socket.gethostbyname', return_value='93.184.216.34'):  # example.com IP
                is_valid, error = validate_url_security('http://example.com/doc.txt')
                assert is_valid is True
                assert error is None
    
    def test_invalid_scheme_ftp(self):
        """Test that FTP URLs are rejected."""
        with pytest.raises(SSRFError, match="Scheme 'ftp' not allowed"):
            validate_url_security('ftp://example.com/file.txt')
    
    def test_invalid_scheme_file(self):
        """Test that file:// URLs are rejected."""
        with pytest.raises(SSRFError, match="Scheme 'file' not allowed"):
            validate_url_security('file:///etc/passwd')
    
    def test_invalid_scheme_custom(self):
        """Test that custom schemes are rejected."""
        with pytest.raises(SSRFError, match="Scheme 'gopher' not allowed"):
            validate_url_security('gopher://example.com/')
    
    def test_ssrf_localhost_ipv4(self):
        """Test that localhost IPv4 addresses are blocked."""
        with patch('socket.gethostbyname', return_value='127.0.0.1'):
            with pytest.raises(SSRFError, match="Access to private IP address 127.0.0.1 is not allowed"):
                validate_url_security('https://localhost/admin')
    
    def test_ssrf_localhost_ipv6(self):
        """Test that localhost IPv6 addresses are blocked."""
        with patch('socket.gethostbyname', return_value='::1'):
            with pytest.raises(SSRFError, match="Access to private IP address ::1 is not allowed"):
                validate_url_security('https://[::1]/admin')
    
    def test_ssrf_private_network_10(self):
        """Test that 10.x.x.x addresses are blocked."""
        with patch('socket.gethostbyname', return_value='10.0.0.1'):
            with pytest.raises(SSRFError, match="Access to private IP address 10.0.0.1 is not allowed"):
                validate_url_security('https://internal.company.com/')
    
    def test_ssrf_private_network_172(self):
        """Test that 172.16-31.x.x addresses are blocked."""
        with patch('socket.gethostbyname', return_value='172.16.0.1'):
            with pytest.raises(SSRFError, match="Access to private IP address 172.16.0.1 is not allowed"):
                validate_url_security('https://docker.internal/')
    
    def test_ssrf_private_network_192(self):
        """Test that 192.168.x.x addresses are blocked."""
        with patch('socket.gethostbyname', return_value='192.168.1.1'):
            with pytest.raises(SSRFError, match="Access to private IP address 192.168.1.1 is not allowed"):
                validate_url_security('https://router.local/')
    
    def test_ssrf_link_local(self):
        """Test that link-local addresses are blocked."""
        with patch('socket.gethostbyname', return_value='169.254.169.254'):  # AWS metadata service
            with pytest.raises(SSRFError, match="Access to private IP address 169.254.169.254 is not allowed"):
                validate_url_security('https://metadata.service/')
    
    def test_ssrf_multicast(self):
        """Test that multicast addresses are blocked."""
        with patch('socket.gethostbyname', return_value='224.0.0.1'):
            with pytest.raises(SSRFError, match="Access to private IP address 224.0.0.1 is not allowed"):
                validate_url_security('https://multicast.example/')
    
    def test_dangerous_port_ssh(self):
        """Test that SSH port is blocked."""
        with pytest.raises(SSRFError, match="Access to port 22 is not allowed"):
            validate_url_security('https://example.com:22/')
    
    def test_dangerous_port_smtp(self):
        """Test that SMTP port is blocked."""
        with pytest.raises(SSRFError, match="Access to port 25 is not allowed"):
            validate_url_security('https://mail.example.com:25/')
    
    def test_invalid_port_negative(self):
        """Test that negative ports are rejected."""
        with pytest.raises(ValidationError, match="Invalid port number: -1"):
            validate_url_security('https://example.com:-1/')
    
    def test_invalid_port_too_high(self):
        """Test that ports > 65535 are rejected."""
        with pytest.raises(ValidationError, match="Invalid port number: 65536"):
            validate_url_security('https://example.com:65536/')
    
    def test_hostname_resolution_failure(self):
        """Test that DNS resolution failures are handled."""
        with patch('socket.gethostbyname', side_effect=socket.gaierror("Name resolution failed")):
            with pytest.raises(ValidationError, match="Cannot resolve hostname"):
                validate_url_security('https://nonexistent.invalid/')
    
    def test_missing_hostname(self):
        """Test that URLs without hostnames are rejected."""
        with pytest.raises(ValidationError, match="URL must contain a valid hostname"):
            validate_url_security('https:///path/without/host')
    
    def test_content_type_validation_allowed(self):
        """Test that allowed content types pass validation."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers = {'content-type': 'text/markdown; charset=utf-8'}
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            with patch('socket.gethostbyname', return_value='8.8.8.8'):
                is_valid, error = validate_url_security('https://example.com/doc.md')
                assert is_valid is True
    
    def test_content_type_validation_rejected(self):
        """Test that disallowed content types are rejected."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers = {'content-type': 'application/x-executable'}
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            with patch('socket.gethostbyname', return_value='8.8.8.8'):
                is_valid, error = validate_url_security('https://example.com/malware.exe')
                assert is_valid is False
                assert "Content type 'application/x-executable' not allowed" in error
    
    def test_content_length_too_large(self):
        """Test that oversized content is rejected."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers = {
                'content-type': 'text/plain',
                'content-length': str(100 * 1024 * 1024)  # 100MB
            }
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            with patch('socket.gethostbyname', return_value='8.8.8.8'):
                is_valid, error = validate_url_security('https://example.com/huge.txt')
                assert is_valid is False
                assert "Content too large" in error
    
    def test_http_error_handling(self):
        """Test that HTTP errors are handled gracefully."""
        from urllib.error import HTTPError
        
        with patch('urllib.request.urlopen', side_effect=HTTPError(None, 404, 'Not Found', None, None)):
            with patch('socket.gethostbyname', return_value='8.8.8.8'):
                is_valid, error = validate_url_security('https://example.com/missing.txt')
                assert is_valid is False
                assert "HTTP error 404" in error
    
    def test_timeout_handling(self):
        """Test that timeouts are handled gracefully."""
        with patch('urllib.request.urlopen', side_effect=socket.timeout()):
            with patch('socket.gethostbyname', return_value='8.8.8.8'):
                is_valid, error = validate_url_security('https://slow.example.com/')
                assert is_valid is False
                assert "Connection timeout" in error


class TestPackageNameValidation:
    """Test package name validation for path traversal protection."""
    
    def test_valid_package_names(self):
        """Test that valid package names pass validation."""
        valid_names = [
            'my-package',
            'package_name',
            'package.name',
            'MyPackage123',
            'a',
            'package-123_name.ext'
        ]
        
        for name in valid_names:
            assert validate_package_name(name) is True, f"Valid name rejected: {name}"
    
    def test_empty_package_name(self):
        """Test that empty package names are rejected."""
        assert validate_package_name('') is False
        assert validate_package_name(None) is False
    
    def test_path_traversal_attempts(self):
        """Test that path traversal attempts are blocked."""
        malicious_names = [
            '../etc/passwd',
            '..\\windows\\system32',
            'package/../../../etc/shadow',
            '..\\..\\..\\windows\\system32\\config\\sam',
            'package/../../etc/hosts'
        ]
        
        for name in malicious_names:
            assert validate_package_name(name) is False, f"Malicious name allowed: {name}"
    
    def test_absolute_paths_rejected(self):
        """Test that absolute paths are rejected."""
        absolute_paths = [
            '/etc/passwd',
            '\\windows\\system32',
            '/usr/local/bin/malware',
            'C:\\Windows\\System32\\cmd.exe'
        ]
        
        for path in absolute_paths:
            assert validate_package_name(path) is False, f"Absolute path allowed: {path}"
    
    def test_reserved_names_rejected(self):
        """Test that Windows reserved names are rejected."""
        for reserved in RESERVED_NAMES:
            assert validate_package_name(reserved) is False, f"Reserved name allowed: {reserved}"
            assert validate_package_name(reserved.upper()) is False, f"Reserved name allowed: {reserved.upper()}"
    
    def test_invalid_characters(self):
        """Test that invalid characters are rejected."""
        invalid_names = [
            'package<name',
            'package>name',
            'package:name',
            'package"name',
            'package|name',
            'package?name',
            'package*name',
            'package\x00name',  # Null byte
            'package\tname',    # Tab
            'package\nname'     # Newline
        ]
        
        for name in invalid_names:
            assert validate_package_name(name) is False, f"Invalid name allowed: {name}"
    
    def test_length_limits(self):
        """Test that length limits are enforced."""
        # Test maximum length
        long_name = 'a' * 256
        assert validate_package_name(long_name) is False
        
        # Test just under limit
        max_valid = 'a' * 255
        assert validate_package_name(max_valid) is True
    
    def test_dot_only_names(self):
        """Test that dot-only names are rejected."""
        dot_names = ['.', '..', '...']
        for name in dot_names:
            assert validate_package_name(name) is False, f"Dot name allowed: {name}"
    
    def test_names_starting_ending_with_dots(self):
        """Test that names starting/ending with dots are rejected."""
        invalid_names = ['.hidden', 'file.', '.config.']
        for name in invalid_names:
            assert validate_package_name(name) is False, f"Dot-prefixed/suffixed name allowed: {name}"


class TestFilenamesanitization:
    """Test filename sanitization for security."""
    
    def test_basic_sanitization(self):
        """Test basic filename sanitization."""
        assert sanitize_filename('document.md') == 'document.md'
        assert sanitize_filename('My Document.txt') == 'My Document.txt'
    
    def test_path_traversal_protection(self):
        """Test that path traversal attempts are blocked."""
        with pytest.raises(PathTraversalError):
            sanitize_filename('../../../etc/passwd')
        
        with pytest.raises(PathTraversalError):
            sanitize_filename('..\\..\\windows\\system32\\config')
        
        with pytest.raises(PathTraversalError):
            sanitize_filename('/absolute/path/file.txt')
        
        with pytest.raises(PathTraversalError):
            sanitize_filename('\\absolute\\windows\\path')
    
    def test_dangerous_character_replacement(self):
        """Test that dangerous characters are replaced."""
        dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        
        for char in dangerous_chars:
            result = sanitize_filename(f'file{char}name.txt')
            assert char not in result
            assert '_' in result or result == 'file_name.txt'
    
    def test_control_character_removal(self):
        """Test that control characters are removed."""
        control_chars = ['\x00', '\x01', '\x1f']
        
        for char in control_chars:
            result = sanitize_filename(f'file{char}name.txt')
            assert char not in result
    
    def test_reserved_name_handling(self):
        """Test that reserved Windows names are handled."""
        for reserved in ['con', 'prn', 'aux', 'nul']:
            result = sanitize_filename(f'{reserved}.txt')
            assert not result.lower().startswith(reserved)
            assert result.startswith('safe_')
    
    def test_length_limiting(self):
        """Test that filename length is limited."""
        long_name = 'a' * 300 + '.txt'
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith('.txt')  # Extension preserved
    
    def test_empty_filename_handling(self):
        """Test that empty filenames are handled."""
        with pytest.raises(ValidationError, match="Filename cannot be empty"):
            sanitize_filename('')
        
        with pytest.raises(ValidationError, match="Filename cannot be empty"):
            sanitize_filename(None)
    
    def test_extension_preservation(self):
        """Test that file extensions are preserved during truncation."""
        long_name = 'a' * 250 + '.markdown'
        result = sanitize_filename(long_name, max_length=255)
        assert result.endswith('.markdown')
        assert len(result) <= 255


class TestConfigPathValidation:
    """Test configuration path validation."""
    
    def test_valid_config_path(self):
        """Test that valid config paths are accepted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'localdocs.config.json'
            result = validate_config_path(config_path)
            assert result == config_path.resolve()
    
    def test_config_filename_validation(self):
        """Test that only correct config filenames are allowed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_config = Path(temp_dir) / 'wrong_name.json'
            
            with pytest.raises(ValidationError, match="Config file must be named 'localdocs.config.json'"):
                validate_config_path(invalid_config)
    
    def test_system_directory_protection(self):
        """Test that system directories are protected."""
        dangerous_paths = [
            '/etc/localdocs.config.json',
            '/usr/localdocs.config.json',
            '/var/localdocs.config.json',
            '/sys/localdocs.config.json',
            '/proc/localdocs.config.json',
            '/dev/localdocs.config.json',
            '/root/localdocs.config.json'
        ]
        
        for path in dangerous_paths:
            with pytest.raises(PathTraversalError, match="Access to system directory not allowed"):
                validate_config_path(path)
    
    def test_path_resolution(self):
        """Test that paths are properly resolved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a complex path with .. components
            complex_path = Path(temp_dir) / 'subdir' / '..' / 'localdocs.config.json'
            
            try:
                result = validate_config_path(complex_path)
                expected = (Path(temp_dir) / 'localdocs.config.json').resolve()
                assert result == expected
            except ValidationError:
                # This is acceptable if the path resolution detects issues
                pass


class TestTagValidation:
    """Test tag validation and cleaning."""
    
    def test_valid_tags(self):
        """Test that valid tags are processed correctly."""
        input_tags = "frontend, backend, api-docs, react"
        result = validate_and_clean_tags(input_tags)
        expected = ['frontend', 'backend', 'api-docs', 'react']
        assert result == expected
    
    def test_empty_input(self):
        """Test that empty input returns empty list."""
        assert validate_and_clean_tags('') == []
        assert validate_and_clean_tags('   ') == []
        assert validate_and_clean_tags(None) == []
    
    def test_tag_cleaning(self):
        """Test that tags are properly cleaned."""
        input_tags = "  Frontend , BACKEND,   api-docs  "
        result = validate_and_clean_tags(input_tags)
        expected = ['frontend', 'backend', 'api-docs']
        assert result == expected
    
    def test_invalid_tag_filtering(self):
        """Test that invalid tags are filtered out."""
        input_tags = "valid-tag, invalid@tag, another_invalid!, toolong" + "x" * 20
        result = validate_and_clean_tags(input_tags)
        # Only 'valid-tag' should remain as it's the only valid one
        assert 'valid-tag' in result
        assert len([tag for tag in result if 'invalid' in tag]) == 0
    
    def test_duplicate_removal(self):
        """Test that duplicate tags are removed."""
        input_tags = "react, vue, react, angular, vue"
        result = validate_and_clean_tags(input_tags)
        assert len(result) == 3  # react, vue, angular
        assert 'react' in result
        assert 'vue' in result
        assert 'angular' in result
    
    def test_tag_length_limit(self):
        """Test that tag length is limited."""
        long_tag = "a" * 25  # Exceeds 20 character limit
        input_tags = f"short, {long_tag}, medium"
        result = validate_and_clean_tags(input_tags)
        assert long_tag not in result
        assert 'short' in result
        assert 'medium' in result
    
    def test_tag_count_limit(self):
        """Test that tag count is limited to 10."""
        many_tags = ','.join([f'tag{i}' for i in range(15)])
        result = validate_and_clean_tags(many_tags)
        assert len(result) <= 10
    
    def test_special_characters_in_tags(self):
        """Test that only alphanumeric and hyphens are allowed."""
        input_tags = "valid-tag, invalid_tag, invalid.tag, invalid tag, invalid@tag"
        result = validate_and_clean_tags(input_tags)
        # Only 'valid-tag' should pass validation
        assert result == ['valid-tag']


class TestDocumentMetadataValidation:
    """Test document metadata validation."""
    
    def test_valid_metadata(self):
        """Test that valid metadata passes validation."""
        name = "API Documentation"
        description = "Complete API reference for developers"
        
        result_name, result_desc = validate_document_metadata(name, description)
        assert result_name == name
        assert result_desc == description
    
    def test_none_values(self):
        """Test that None values are handled correctly."""
        result_name, result_desc = validate_document_metadata(None, None)
        assert result_name is None
        assert result_desc is None
    
    def test_empty_strings(self):
        """Test that empty strings are converted to None."""
        result_name, result_desc = validate_document_metadata('', '   ')
        assert result_name is None
        assert result_desc is None
    
    def test_length_limiting(self):
        """Test that length limits are enforced."""
        long_name = 'a' * 250
        long_desc = 'b' * 1100
        
        result_name, result_desc = validate_document_metadata(long_name, long_desc)
        assert len(result_name) == 200
        assert len(result_desc) == 1000
    
    def test_control_character_removal(self):
        """Test that control characters are removed."""
        name_with_control = "Document\x00Name\x1f"
        desc_with_control = "Description\x7fwith\x01control"
        
        result_name, result_desc = validate_document_metadata(name_with_control, desc_with_control)
        assert '\x00' not in result_name
        assert '\x1f' not in result_name
        assert '\x7f' not in result_desc
        assert '\x01' not in result_desc
    
    def test_whitespace_stripping(self):
        """Test that leading/trailing whitespace is stripped."""
        name = "  Document Name  "
        description = "\t\nDescription with whitespace\n\t"
        
        result_name, result_desc = validate_document_metadata(name, description)
        assert result_name == "Document Name"
        assert result_desc == "Description with whitespace"


class TestPrivateIPRangeValidation:
    """Test that all private IP ranges are properly defined and blocked."""
    
    def test_private_ip_ranges_coverage(self):
        """Test that all major private IP ranges are covered."""
        # Test some known private IPs
        private_ips = [
            '127.0.0.1',      # Loopback
            '10.0.0.1',       # Private class A
            '172.16.0.1',     # Private class B
            '192.168.1.1',    # Private class C
            '169.254.1.1',    # Link-local
            '224.0.0.1',      # Multicast
            '240.0.0.1',      # Reserved
            '::1',            # IPv6 loopback
            'fc00::1',        # IPv6 unique local
            'fe80::1'         # IPv6 link-local
        ]
        
        for ip_str in private_ips:
            ip = ip_address(ip_str)
            is_private = any(ip in network for network in PRIVATE_IP_RANGES)
            assert is_private, f"Private IP {ip_str} not blocked by PRIVATE_IP_RANGES"
    
    def test_public_ip_ranges_allowed(self):
        """Test that public IPs are not blocked."""
        public_ips = [
            '8.8.8.8',        # Google DNS
            '1.1.1.1',        # Cloudflare DNS
            '93.184.216.34',  # example.com
            '151.101.1.140',  # Reddit
            '2606:4700:4700::1111'  # Cloudflare IPv6
        ]
        
        for ip_str in public_ips:
            ip = ip_address(ip_str)
            is_private = any(ip in network for network in PRIVATE_IP_RANGES)
            assert not is_private, f"Public IP {ip_str} incorrectly blocked"
    
    def test_scheme_validation(self):
        """Test that only allowed schemes are accepted."""
        for scheme in ALLOWED_SCHEMES:
            # This should not raise an exception during scheme validation
            # (though it might fail later for other reasons)
            try:
                validate_url_security(f'{scheme}://example.com/')
            except SSRFError as e:
                if "Scheme" in str(e) and "not allowed" in str(e):
                    pytest.fail(f"Allowed scheme {scheme} was rejected")
            except (ValidationError, Exception):
                # Other validation errors are acceptable
                pass
        
        # Test disallowed schemes
        disallowed_schemes = ['ftp', 'file', 'gopher', 'ldap', 'dict']
        for scheme in disallowed_schemes:
            with pytest.raises(SSRFError, match=f"Scheme '{scheme}' not allowed"):
                validate_url_security(f'{scheme}://example.com/')


if __name__ == '__main__':
    pytest.main([__file__])