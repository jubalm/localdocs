"""
Command-line interface for LocalDocs.

This module provides the main CLI entry point with comprehensive argument parsing,
command routing, and error handling with security focus.
"""

import sys
import argparse
from typing import List, Optional
import asyncio

from .exceptions import (
    LocalDocsError,
    ValidationError,
    NetworkError,
    DownloadError,
    DocumentNotFoundError,
    PackagingError,
    ConfigurationError,
    InteractiveError
)
from .managers import DocManager, InteractiveManager
from .utils import validate_and_clean_tags


class CLIError(LocalDocsError):
    """Exception raised for CLI-specific errors."""
    pass


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser with comprehensive validation.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="LocalDocs - Secure documentation downloader optimized for LLM workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  localdocs add https://example.com/doc.md
  localdocs add -f urls.txt
  localdocs set abc123de -n "API Documentation" -d "Complete API reference"
  localdocs extract --format json --tags frontend,react
  localdocs package my-docs --format claude --include abc123de,def456gh
  localdocs manage

For more information, visit: https://github.com/your-org/localdocs
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add command
    add_parser = subparsers.add_parser(
        'add', 
        help='Download documents from URLs',
        description='Download and add documents to the collection with security validation'
    )
    add_parser.add_argument(
        'urls', 
        nargs='*', 
        help='URLs to download (supports HTTP/HTTPS only)'
    )
    add_parser.add_argument(
        '-f', '--from-file', 
        help='Read URLs from file (one per line, # for comments)',
        metavar='FILE'
    )
    add_parser.add_argument(
        '--async', 
        action='store_true', 
        help='Use asynchronous downloads for better performance'
    )
    
    # Set command  
    set_parser = subparsers.add_parser(
        'set', 
        help='Set document metadata',
        description='Set name, description, and tags for a document'
    )
    set_parser.add_argument(
        'hash_id', 
        help='Document hash ID (8-character identifier)'
    )
    set_parser.add_argument(
        '-n', '--name', 
        help='Document name (max 200 characters)',
        metavar='NAME'
    )
    set_parser.add_argument(
        '-d', '--description', 
        help='Document description (max 1000 characters)',
        metavar='DESC'
    )
    set_parser.add_argument(
        '-t', '--tags', 
        help='Comma-separated tags (max 10 tags, alphanumeric + hyphens, max 20 chars each)',
        metavar='TAGS'
    )
    
    # Extract command
    extract_parser = subparsers.add_parser(
        'extract', 
        help='Extract data from documents',
        description='Extract and filter document data with multiple output formats'
    )
    extract_parser.add_argument(
        '--format', 
        choices=['table', 'json', 'csv', 'ids'], 
        default='table', 
        help='Output format (default: table)'
    )
    extract_parser.add_argument(
        '--fields', 
        help='Comma-separated field list: id,name,description,tags,url',
        metavar='FIELDS'
    )
    extract_parser.add_argument(
        '--tags', 
        help='Filter by tags (comma-separated, OR logic)',
        metavar='TAGS'
    )
    extract_parser.add_argument(
        '--has-tags', 
        action='store_true', 
        help='Only show documents with tags'
    )
    extract_parser.add_argument(
        '--no-tags', 
        action='store_true', 
        help='Only show documents without tags'
    )
    extract_parser.add_argument(
        '--name-contains', 
        help='Filter by name containing text (case-insensitive)',
        metavar='TEXT'
    )
    extract_parser.add_argument(
        '--desc-contains', 
        help='Filter by description containing text (case-insensitive)',
        metavar='TEXT'
    )
    extract_parser.add_argument(
        '--sort-by', 
        choices=['id', 'name', 'url', 'tags'], 
        default='id', 
        help='Sort results by field (default: id)'
    )
    extract_parser.add_argument(
        '--reverse', 
        action='store_true', 
        help='Reverse sort order'
    )
    extract_parser.add_argument(
        '--limit', 
        type=int, 
        help='Limit number of results',
        metavar='N'
    )
    extract_parser.add_argument(
        '--quiet', 
        action='store_true', 
        help='No headers or summaries in output'
    )
    extract_parser.add_argument(
        '--count-only', 
        action='store_true', 
        help='Output only count of matching documents'
    )
    extract_parser.add_argument(
        '--output', 
        help='Write output to file instead of stdout',
        metavar='FILE'
    )
    
    # Update command
    update_parser = subparsers.add_parser(
        'update', 
        help='Update documents from their original URLs',
        description='Re-download documents to get latest content'
    )
    update_parser.add_argument(
        'hash_id', 
        nargs='?', 
        help='Specific document to update (if not provided, updates all)'
    )
    update_parser.add_argument(
        '--async', 
        action='store_true', 
        help='Use asynchronous downloads for better performance'
    )
    
    # Remove command
    remove_parser = subparsers.add_parser(
        'remove', 
        help='Remove document from collection',
        description='Permanently remove a document and its file'
    )
    remove_parser.add_argument(
        'hash_id', 
        help='Document hash ID to remove'
    )
    
    # Package command
    package_parser = subparsers.add_parser(
        'package', 
        help='Create documentation packages',
        description='Package documents for distribution in various formats'
    )
    package_parser.add_argument(
        'package_name', 
        help='Package directory name (alphanumeric, hyphens, underscores, dots only)'
    )
    package_parser.add_argument(
        '--format', 
        choices=['toc', 'claude', 'json'], 
        default='toc', 
        help='Package format (default: toc)'
    )
    package_parser.add_argument(
        '--soft-links', 
        action='store_true',
        help='Use absolute paths without copying files (not recommended for distribution)'
    )
    package_parser.add_argument(
        '--include', 
        help='Comma-separated list of document IDs to include (default: all)',
        metavar='IDS'
    )
    package_parser.add_argument(
        '--tags',
        help='Filter by tags (comma-separated, OR logic) - can combine with --include',
        metavar='TAGS'
    )
    
    # Manage command
    manage_parser = subparsers.add_parser(
        'manage', 
        help='Interactive document manager',
        description='Launch interactive terminal interface for document management'
    )
    
    return parser


def handle_add_command(args, manager: DocManager) -> int:
    """
    Handle the add command with comprehensive error handling.
    
    Args:
        args: Parsed command arguments
        manager: DocManager instance
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        if args.from_file:
            count = manager.add_from_file(args.from_file, getattr(args, 'async', False))
            return 0 if count > 0 else 1
        elif args.urls:
            count = manager.add_multiple(args.urls, getattr(args, 'async', False))
            return 0 if count > 0 else 1
        else:
            # Interactive URL input
            print("Enter URLs (one per line, empty line to finish):")
            urls = []
            
            while True:
                try:
                    url = input("> ").strip()
                    if not url:
                        break
                    
                    # Basic URL validation
                    if not (url.startswith('http://') or url.startswith('https://')):
                        print(f"Warning: Skipping invalid URL: {url}")
                        continue
                        
                    urls.append(url)
                except KeyboardInterrupt:
                    print("\nCancelled")
                    return 1
            
            if urls:
                count = manager.add_multiple(urls, getattr(args, 'async', False))
                return 0 if count > 0 else 1
            else:
                print("No URLs entered")
                return 0
                
    except ValidationError as e:
        print(f"Validation error: {e}")
        return 1
    except NetworkError as e:
        print(f"Network error: {e}")
        return 1
    except Exception as e:
        print(f"Error adding documents: {e}")
        return 1


def handle_set_command(args, manager: DocManager) -> int:
    """
    Handle the set command with validation.
    
    Args:
        args: Parsed command arguments
        manager: DocManager instance
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Validate that at least one field is provided
        if not any([args.name, args.description, args.tags]):
            print("Error: At least one of --name, --description, or --tags must be provided")
            return 1
        
        success = manager.set_metadata(args.hash_id, args.name, args.description, args.tags)
        return 0 if success else 1
        
    except DocumentNotFoundError as e:
        print(f"Document not found: {e}")
        return 1
    except ValidationError as e:
        print(f"Validation error: {e}")
        return 1
    except Exception as e:
        print(f"Error setting metadata: {e}")
        return 1


def handle_extract_command(args, manager: DocManager) -> int:
    """
    Handle the extract command with comprehensive filtering.
    
    Args:
        args: Parsed command arguments
        manager: DocManager instance
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Parse fields if provided
        fields = None
        if args.fields:
            fields = [field.strip() for field in args.fields.split(',') if field.strip()]
            # Validate field names
            valid_fields = {'id', 'name', 'description', 'tags', 'url'}
            invalid_fields = set(fields) - valid_fields
            if invalid_fields:
                print(f"Error: Invalid field names: {', '.join(invalid_fields)}")
                print(f"Valid fields: {', '.join(sorted(valid_fields))}")
                return 1
        
        # Parse tag filters
        tag_filters = None
        if args.tags:
            tag_filters = validate_and_clean_tags(args.tags)
            if not tag_filters:
                print("Warning: No valid tags found in filter")
        
        # Validate conflicting options
        if args.has_tags and args.no_tags:
            print("Error: Cannot use both --has-tags and --no-tags")
            return 1
        
        # Validate limit
        if args.limit is not None and args.limit <= 0:
            print("Error: Limit must be a positive number")
            return 1
        
        success = manager.extract_data(
            format_type=args.format,
            tag_filters=tag_filters,
            fields=fields,
            has_tags=args.has_tags,
            no_tags=args.no_tags,
            name_contains=args.name_contains,
            desc_contains=args.desc_contains,
            sort_by=args.sort_by,
            reverse=args.reverse,
            limit=args.limit,
            quiet=args.quiet,
            count_only=args.count_only,
            output_file=args.output
        )
        
        return 0 if success else 1
        
    except ValidationError as e:
        print(f"Validation error: {e}")
        return 1
    except Exception as e:
        print(f"Error extracting data: {e}")
        return 1


def handle_update_command(args, manager: DocManager) -> int:
    """
    Handle the update command.
    
    Args:
        args: Parsed command arguments
        manager: DocManager instance
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        use_async = getattr(args, 'async', False)
        
        if args.hash_id:
            success = manager.update_doc(args.hash_id, use_async)
            return 0 if success else 1
        else:
            count = manager.update_all(use_async)
            return 0 if count > 0 else 1
            
    except DocumentNotFoundError as e:
        print(f"Document not found: {e}")
        return 1
    except NetworkError as e:
        print(f"Network error: {e}")
        return 1
    except Exception as e:
        print(f"Error updating documents: {e}")
        return 1


def handle_remove_command(args, manager: DocManager) -> int:
    """
    Handle the remove command.
    
    Args:
        args: Parsed command arguments
        manager: DocManager instance
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        success = manager.remove_doc(args.hash_id)
        return 0 if success else 1
        
    except DocumentNotFoundError as e:
        print(f"Document not found: {e}")
        return 1
    except Exception as e:
        print(f"Error removing document: {e}")
        return 1


def handle_package_command(args, manager: DocManager) -> int:
    """
    Handle the package command with filtering support.
    
    Args:
        args: Parsed command arguments
        manager: DocManager instance
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Determine which documents to package
        if args.include or args.tags:
            # Start with all documents
            all_docs = manager.config.get("documents", {})
            selected_docs = all_docs.copy()
            
            # Apply tag filtering if specified
            if args.tags:
                tag_filters = validate_and_clean_tags(args.tags)
                if tag_filters:
                    selected_docs = manager._filter_docs_by_tags(selected_docs, tag_filters)
                else:
                    print("Warning: No valid tags found in filter")
                    selected_docs = {}
            
            # Apply ID filtering if specified (further narrows selection)
            if args.include:
                include_doc_ids = [doc_id.strip() for doc_id in args.include.split(',') if doc_id.strip()]
                # Keep only docs that are both in tag filter results AND in include list
                selected_docs = {doc_id: metadata for doc_id, metadata in selected_docs.items() 
                               if doc_id in include_doc_ids}
            
            # Package selected documents
            include_docs = list(selected_docs.keys())
            if include_docs:
                success = manager.package_selected_docs(
                    args.package_name, include_docs, args.format, args.soft_links
                )
                return 0 if success else 1
            else:
                print("No documents match the specified criteria")
                return 1
        else:
            # Package all documents (existing behavior)
            success = manager.package_all_docs(args.package_name, args.format, args.soft_links)
            return 0 if success else 1
            
    except ValidationError as e:
        print(f"Validation error: {e}")
        return 1
    except PackagingError as e:
        print(f"Packaging error: {e}")
        return 1
    except Exception as e:
        print(f"Error creating package: {e}")
        return 1


def handle_manage_command(args, manager: DocManager) -> int:
    """
    Handle the manage command (interactive mode).
    
    Args:
        args: Parsed command arguments
        manager: DocManager instance
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        interactive = InteractiveManager(manager)
        success = interactive.run()
        return 0 if success else 1
        
    except InteractiveError as e:
        print(f"Interactive mode error: {e}")
        return 1
    except Exception as e:
        print(f"Error in interactive mode: {e}")
        return 1


def main() -> int:
    """
    Main CLI entry point with comprehensive error handling.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        parser = create_argument_parser()
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return 1
        
        # Initialize DocManager with error handling
        try:
            manager = DocManager()
        except ConfigurationError as e:
            print(f"Configuration error: {e}")
            return 1
        except Exception as e:
            print(f"Failed to initialize LocalDocs: {e}")
            return 1
        
        # Route to appropriate command handler
        command_handlers = {
            'add': handle_add_command,
            'set': handle_set_command,
            'extract': handle_extract_command,
            'update': handle_update_command,
            'remove': handle_remove_command,
            'package': handle_package_command,
            'manage': handle_manage_command
        }
        
        handler = command_handlers.get(args.command)
        if not handler:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            return 1
        
        return handler(args, manager)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except BrokenPipeError:
        # Handle broken pipe gracefully (e.g., when piping to head)
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def cli_main() -> None:
    """
    Entry point for the CLI that calls sys.exit with appropriate code.
    
    This function is used as the entry point in setup.py/pyproject.toml.
    """
    sys.exit(main())


if __name__ == "__main__":
    cli_main()