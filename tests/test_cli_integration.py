"""
Integration tests for CLI commands with mocked network operations.

This module tests the complete CLI functionality with proper mocking
to avoid real network requests while ensuring security and functionality.
"""

import pytest
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from io import StringIO
import sys

from localdocs.cli import main, create_argument_parser
from localdocs.managers import DocManager
from localdocs.exceptions import ValidationError, NetworkError, DocumentNotFoundError


@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        config_file = config_dir / "localdocs.config.json"
        
        # Create initial config
        initial_config = {
            "storage_directory": ".",
            "documents": {}
        }
        
        with open(config_file, 'w') as f:
            json.dump(initial_config, f)
        
        yield config_dir


@pytest.fixture
def mock_network_success():
    """Mock successful network operations."""
    with patch('localdocs.utils.network.validate_url_sync', return_value=True), \
         patch('localdocs.utils.network.download_content_sync', return_value="# Test Document\n\nThis is a test document."), \
         patch('localdocs.utils.validation.validate_url_security', return_value=(True, None)):
        yield


@pytest.fixture
def mock_network_failure():
    """Mock network operation failures."""
    with patch('localdocs.utils.network.validate_url_sync', side_effect=NetworkError("Network error")), \
         patch('localdocs.utils.network.download_content_sync', side_effect=NetworkError("Download failed")):
        yield


@pytest.fixture
def populated_config_dir():
    """Create a config directory with some test documents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        config_file = config_dir / "localdocs.config.json"
        
        # Create test documents
        test_config = {
            "storage_directory": ".",
            "documents": {
                "abc123de": {
                    "url": "https://example.com/doc1.md",
                    "name": "Test Document 1",
                    "description": "First test document",
                    "tags": ["test", "frontend"]
                },
                "def456gh": {
                    "url": "https://example.com/doc2.md", 
                    "name": "Test Document 2",
                    "description": "Second test document",
                    "tags": ["test", "backend"]
                },
                "ghi789jk": {
                    "url": "https://example.com/doc3.md",
                    "name": None,
                    "description": None,
                    "tags": []
                }
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Create corresponding markdown files
        for doc_id in test_config["documents"]:
            doc_file = config_dir / f"{doc_id}.md"
            with open(doc_file, 'w') as f:
                f.write(f"# Document {doc_id}\n\nContent for {doc_id}")
        
        yield config_dir


class TestCLIArgumentParsing:
    """Test command-line argument parsing."""
    
    def test_no_command_shows_help(self, capsys):
        """Test that running without command shows help."""
        with patch('sys.argv', ['localdocs']):
            parser = create_argument_parser()
            args = parser.parse_args([])
            assert args.command is None
    
    def test_add_command_parsing(self):
        """Test add command argument parsing."""
        parser = create_argument_parser()
        
        # Test with URLs
        args = parser.parse_args(['add', 'https://example.com/doc1.md', 'https://example.com/doc2.md'])
        assert args.command == 'add'
        assert args.urls == ['https://example.com/doc1.md', 'https://example.com/doc2.md']
        
        # Test with file
        args = parser.parse_args(['add', '-f', 'urls.txt'])
        assert args.command == 'add'
        assert args.from_file == 'urls.txt'
    
    def test_set_command_parsing(self):
        """Test set command argument parsing."""
        parser = create_argument_parser()
        
        args = parser.parse_args(['set', 'abc123de', '-n', 'Document Name', '-d', 'Description', '-t', 'tag1,tag2'])
        assert args.command == 'set'
        assert args.hash_id == 'abc123de'
        assert args.name == 'Document Name'
        assert args.description == 'Description'
        assert args.tags == 'tag1,tag2'
    
    def test_extract_command_parsing(self):
        """Test extract command argument parsing."""
        parser = create_argument_parser()
        
        args = parser.parse_args(['extract', '--format', 'json', '--tags', 'frontend,backend', '--sort-by', 'name'])
        assert args.command == 'extract'
        assert args.format == 'json'
        assert args.tags == 'frontend,backend'
        assert args.sort_by == 'name'
    
    def test_package_command_parsing(self):
        """Test package command argument parsing."""
        parser = create_argument_parser()
        
        args = parser.parse_args(['package', 'my-package', '--format', 'claude', '--include', 'abc123de,def456gh'])
        assert args.command == 'package'
        assert args.package_name == 'my-package'
        assert args.format == 'claude'
        assert args.include == 'abc123de,def456gh'


class TestAddCommand:
    """Test the add command functionality."""
    
    def test_add_single_url_success(self, temp_config_dir, mock_network_success, capsys):
        """Test adding a single URL successfully."""
        with patch('localdocs.utils.config.ConfigManager') as mock_config_manager:
            mock_manager = MagicMock()
            mock_manager.config_path = temp_config_dir / "localdocs.config.json"
            mock_manager.base_dir = temp_config_dir
            mock_config_manager.return_value = mock_manager
            
            with patch('sys.argv', ['localdocs', 'add', 'https://example.com/doc.md']):
                with patch('localdocs.managers.DocManager') as mock_doc_manager:
                    mock_doc_manager.return_value.add_multiple.return_value = 1
                    
                    result = main()
                    assert result == 0
                    mock_doc_manager.return_value.add_multiple.assert_called_once()
    
    def test_add_multiple_urls_success(self, temp_config_dir, mock_network_success):
        """Test adding multiple URLs successfully."""
        with patch('sys.argv', ['localdocs', 'add', 'https://example.com/doc1.md', 'https://example.com/doc2.md']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.add_multiple.return_value = 2
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.add_multiple.assert_called_once_with(
                    ['https://example.com/doc1.md', 'https://example.com/doc2.md'], False
                )
    
    def test_add_from_file_success(self, temp_config_dir, mock_network_success):
        """Test adding URLs from file successfully."""
        # Create test file with URLs
        urls_file = temp_config_dir / "test_urls.txt"
        with open(urls_file, 'w') as f:
            f.write("https://example.com/doc1.md\n")
            f.write("# This is a comment\n")
            f.write("https://example.com/doc2.md\n")
            f.write("\n")  # Empty line
        
        with patch('sys.argv', ['localdocs', 'add', '-f', str(urls_file)]):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.add_from_file.return_value = 2
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.add_from_file.assert_called_once()
    
    def test_add_network_failure(self, temp_config_dir, mock_network_failure):
        """Test handling network failures during add."""
        with patch('sys.argv', ['localdocs', 'add', 'https://example.com/doc.md']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.add_multiple.return_value = 0  # No successful downloads
                
                result = main()
                assert result == 1  # Should return error code
    
    def test_add_interactive_mode(self, temp_config_dir, mock_network_success):
        """Test interactive URL input mode."""
        user_input = "https://example.com/doc1.md\nhttps://example.com/doc2.md\n\n"
        
        with patch('sys.argv', ['localdocs', 'add']):
            with patch('builtins.input', side_effect=user_input.split('\n')):
                with patch('localdocs.managers.DocManager') as mock_doc_manager:
                    mock_doc_manager.return_value.add_multiple.return_value = 2
                    
                    result = main()
                    assert result == 0
    
    def test_add_invalid_urls_filtered(self, temp_config_dir, capsys):
        """Test that invalid URLs are filtered out in interactive mode."""
        user_input = "not-a-url\nftp://invalid.com/file\nhttps://valid.com/doc.md\n\n"
        
        with patch('sys.argv', ['localdocs', 'add']):
            with patch('builtins.input', side_effect=user_input.split('\n')):
                with patch('localdocs.managers.DocManager') as mock_doc_manager:
                    mock_doc_manager.return_value.add_multiple.return_value = 1
                    
                    result = main()
                    captured = capsys.readouterr()
                    assert "Warning: Skipping invalid URL" in captured.out


class TestSetCommand:
    """Test the set command functionality."""
    
    def test_set_metadata_success(self, populated_config_dir):
        """Test setting metadata successfully."""
        with patch('sys.argv', ['localdocs', 'set', 'abc123de', '-n', 'New Name', '-d', 'New Description']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.set_metadata.return_value = True
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.set_metadata.assert_called_once_with(
                    'abc123de', 'New Name', 'New Description', None
                )
    
    def test_set_tags_only(self, populated_config_dir):
        """Test setting only tags."""
        with patch('sys.argv', ['localdocs', 'set', 'abc123de', '-t', 'new-tag,another-tag']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.set_metadata.return_value = True
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.set_metadata.assert_called_once_with(
                    'abc123de', None, None, 'new-tag,another-tag'
                )
    
    def test_set_no_fields_error(self, populated_config_dir, capsys):
        """Test error when no fields are provided."""
        with patch('sys.argv', ['localdocs', 'set', 'abc123de']):
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "At least one of --name, --description, or --tags must be provided" in captured.out
    
    def test_set_document_not_found(self, populated_config_dir, capsys):
        """Test handling document not found."""
        with patch('sys.argv', ['localdocs', 'set', 'nonexistent', '-n', 'Name']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.set_metadata.side_effect = DocumentNotFoundError("Document not found")
                
                result = main()
                assert result == 1
                captured = capsys.readouterr()
                assert "Document not found" in captured.out


class TestExtractCommand:
    """Test the extract command functionality."""
    
    def test_extract_table_format(self, populated_config_dir):
        """Test extracting data in table format."""
        with patch('sys.argv', ['localdocs', 'extract']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.extract_data.return_value = True
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.extract_data.assert_called_once()
    
    def test_extract_json_format_with_filters(self, populated_config_dir):
        """Test extracting data in JSON format with filters."""
        with patch('sys.argv', ['localdocs', 'extract', '--format', 'json', '--tags', 'frontend', '--has-tags']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.extract_data.return_value = True
                mock_doc_manager.return_value._validate_and_clean_tags.return_value = ['frontend']
                
                result = main()
                assert result == 0
    
    def test_extract_with_invalid_fields(self, populated_config_dir, capsys):
        """Test extract with invalid field names."""
        with patch('sys.argv', ['localdocs', 'extract', '--fields', 'id,invalid_field,name']):
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "Invalid field names: invalid_field" in captured.out
    
    def test_extract_conflicting_tag_options(self, populated_config_dir, capsys):
        """Test extract with conflicting tag options."""
        with patch('sys.argv', ['localdocs', 'extract', '--has-tags', '--no-tags']):
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "Cannot use both --has-tags and --no-tags" in captured.out
    
    def test_extract_invalid_limit(self, populated_config_dir, capsys):
        """Test extract with invalid limit value."""
        with patch('sys.argv', ['localdocs', 'extract', '--limit', '0']):
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "Limit must be a positive number" in captured.out
    
    def test_extract_count_only(self, populated_config_dir):
        """Test extract with count-only option."""
        with patch('sys.argv', ['localdocs', 'extract', '--count-only']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.extract_data.return_value = True
                
                result = main()
                assert result == 0
                # Verify count_only parameter is passed
                call_args = mock_doc_manager.return_value.extract_data.call_args
                assert call_args.kwargs['count_only'] is True


class TestUpdateCommand:
    """Test the update command functionality."""
    
    def test_update_single_document(self, populated_config_dir, mock_network_success):
        """Test updating a single document."""
        with patch('sys.argv', ['localdocs', 'update', 'abc123de']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.update_doc.return_value = True
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.update_doc.assert_called_once_with('abc123de', False)
    
    def test_update_all_documents(self, populated_config_dir, mock_network_success):
        """Test updating all documents."""
        with patch('sys.argv', ['localdocs', 'update']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.update_all.return_value = 2
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.update_all.assert_called_once_with(False)
    
    def test_update_with_async(self, populated_config_dir, mock_network_success):
        """Test updating with async option."""
        with patch('sys.argv', ['localdocs', 'update', '--async']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.update_all.return_value = 2
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.update_all.assert_called_once_with(True)
    
    def test_update_document_not_found(self, populated_config_dir, capsys):
        """Test updating non-existent document."""
        with patch('sys.argv', ['localdocs', 'update', 'nonexistent']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.update_doc.side_effect = DocumentNotFoundError("Document not found")
                
                result = main()
                assert result == 1
                captured = capsys.readouterr()
                assert "Document not found" in captured.out


class TestRemoveCommand:
    """Test the remove command functionality."""
    
    def test_remove_document_success(self, populated_config_dir):
        """Test removing a document successfully."""
        with patch('sys.argv', ['localdocs', 'remove', 'abc123de']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.remove_doc.return_value = True
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.remove_doc.assert_called_once_with('abc123de')
    
    def test_remove_document_not_found(self, populated_config_dir, capsys):
        """Test removing non-existent document."""
        with patch('sys.argv', ['localdocs', 'remove', 'nonexistent']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.remove_doc.side_effect = DocumentNotFoundError("Document not found")
                
                result = main()
                assert result == 1
                captured = capsys.readouterr()
                assert "Document not found" in captured.out


class TestPackageCommand:
    """Test the package command functionality."""
    
    def test_package_all_documents(self, populated_config_dir):
        """Test packaging all documents."""
        with patch('sys.argv', ['localdocs', 'package', 'my-package']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.package_all_docs.return_value = True
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.package_all_docs.assert_called_once_with('my-package', 'toc', False)
    
    def test_package_with_format_and_options(self, populated_config_dir):
        """Test packaging with specific format and options."""
        with patch('sys.argv', ['localdocs', 'package', 'claude-docs', '--format', 'claude', '--soft-links']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.package_all_docs.return_value = True
                
                result = main()
                assert result == 0
                mock_doc_manager.return_value.package_all_docs.assert_called_once_with('claude-docs', 'claude', True)
    
    def test_package_with_include_filter(self, populated_config_dir):
        """Test packaging with include filter."""
        with patch('sys.argv', ['localdocs', 'package', 'filtered-package', '--include', 'abc123de,def456gh']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                # Mock config data
                mock_doc_manager.return_value.config = {
                    "documents": {
                        "abc123de": {"name": "Doc 1"},
                        "def456gh": {"name": "Doc 2"},
                        "ghi789jk": {"name": "Doc 3"}
                    }
                }
                mock_doc_manager.return_value.package_selected_docs.return_value = True
                
                result = main()
                assert result == 0
                # Should call package_selected_docs with the filtered documents
                mock_doc_manager.return_value.package_selected_docs.assert_called_once()
    
    def test_package_with_tag_filter(self, populated_config_dir):
        """Test packaging with tag filter."""
        with patch('sys.argv', ['localdocs', 'package', 'frontend-docs', '--tags', 'frontend']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.config = {"documents": {"abc123de": {"tags": ["frontend"]}}}
                mock_doc_manager.return_value._filter_docs_by_tags.return_value = {"abc123de": {"tags": ["frontend"]}}
                mock_doc_manager.return_value._validate_and_clean_tags.return_value = ['frontend']
                mock_doc_manager.return_value.package_selected_docs.return_value = True
                
                result = main()
                assert result == 0
    
    def test_package_no_matching_documents(self, populated_config_dir, capsys):
        """Test packaging when no documents match criteria."""
        with patch('sys.argv', ['localdocs', 'package', 'empty-package', '--include', 'nonexistent']):
            with patch('localdocs.managers.DocManager') as mock_doc_manager:
                mock_doc_manager.return_value.config = {"documents": {}}
                
                result = main()
                assert result == 1
                captured = capsys.readouterr()
                assert "No documents match the specified criteria" in captured.out


class TestManageCommand:
    """Test the manage command functionality."""
    
    def test_manage_command_success(self, populated_config_dir):
        """Test launching interactive manager successfully."""
        with patch('sys.argv', ['localdocs', 'manage']):
            with patch('localdocs.managers.InteractiveManager') as mock_interactive:
                mock_interactive.return_value.run.return_value = True
                
                result = main()
                assert result == 0
                mock_interactive.assert_called_once()
                mock_interactive.return_value.run.assert_called_once()
    
    def test_manage_command_failure(self, populated_config_dir, capsys):
        """Test handling interactive manager failure."""
        with patch('sys.argv', ['localdocs', 'manage']):
            with patch('localdocs.managers.InteractiveManager') as mock_interactive:
                mock_interactive.return_value.run.return_value = False
                
                result = main()
                assert result == 1


class TestErrorHandling:
    """Test comprehensive error handling across CLI."""
    
    def test_keyboard_interrupt_handling(self, temp_config_dir, capsys):
        """Test handling of keyboard interrupts."""
        with patch('sys.argv', ['localdocs', 'add', 'https://example.com/doc.md']):
            with patch('localdocs.managers.DocManager', side_effect=KeyboardInterrupt()):
                result = main()
                assert result == 1
                captured = capsys.readouterr()
                assert "Operation cancelled by user" in captured.out
    
    def test_configuration_error_handling(self, capsys):
        """Test handling of configuration errors."""
        with patch('sys.argv', ['localdocs', 'extract']):
            with patch('localdocs.managers.DocManager', side_effect=Exception("Config error")):
                result = main()
                assert result == 1
                captured = capsys.readouterr()
                assert "Failed to initialize LocalDocs" in captured.out
    
    def test_broken_pipe_handling(self):
        """Test graceful handling of broken pipes."""
        with patch('sys.argv', ['localdocs', 'extract']):
            with patch('localdocs.managers.DocManager', side_effect=BrokenPipeError()):
                result = main()
                assert result == 0  # Should handle gracefully
    
    def test_unknown_command_handling(self, capsys):
        """Test handling of unknown commands."""
        # This would need to be tested by manipulating the parser state
        # or by testing the command routing logic directly
        pass


class TestConfigurationManagement:
    """Test configuration file management in CLI context."""
    
    def test_config_auto_discovery(self, temp_config_dir):
        """Test automatic config discovery."""
        # Change to temp directory to test CWD discovery
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_config_dir)
            
            with patch('sys.argv', ['localdocs', 'extract']):
                with patch('localdocs.managers.DocManager') as mock_doc_manager:
                    mock_doc_manager.return_value.extract_data.return_value = True
                    
                    result = main()
                    assert result == 0
                    
        finally:
            os.chdir(original_cwd)
    
    def test_empty_config_handling(self, temp_config_dir, capsys):
        """Test handling of empty configuration."""
        # Remove all documents from config
        config_file = temp_config_dir / "localdocs.config.json"
        with open(config_file, 'w') as f:
            json.dump({"storage_directory": ".", "documents": {}}, f)
        
        with patch('sys.argv', ['localdocs', 'extract']):
            with patch('localdocs.utils.config.ConfigManager') as mock_config_manager:
                mock_manager = MagicMock()
                mock_manager.config_path = config_file
                mock_manager.base_dir = temp_config_dir
                mock_manager.load_config.return_value = {"storage_directory": ".", "documents": {}}
                mock_config_manager.return_value = mock_manager
                
                result = main()
                assert result == 0  # Should handle empty config gracefully


if __name__ == '__main__':
    pytest.main([__file__])