"""
Document Manager for LocalDocs.

This module provides the core document management functionality with
security-focused validation, async support, and proper error handling.
"""

import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import asyncio

from ..exceptions import (
    LocalDocsError,
    ValidationError,
    NetworkError,
    DownloadError,
    DocumentNotFoundError,
    PackagingError,
    ConfigurationError
)
from ..utils import (
    ConfigManager,
    create_config_manager,
    validate_package_name,
    sanitize_filename,
    validate_and_clean_tags,
    validate_document_metadata,
    download_content_sync,
    download_content_async,
    validate_url_sync
)


class DocManager:
    """
    Secure document manager with comprehensive validation and error handling.
    
    This class provides all core document management functionality including
    downloading, metadata management, packaging, and update operations.
    """
    
    def __init__(self, config_path: Optional[str] = None, enable_cache: bool = True):
        """
        Initialize document manager.
        
        Args:
            config_path: Optional explicit config path
            enable_cache: Whether to enable configuration caching
            
        Raises:
            ConfigurationError: If configuration cannot be loaded
        """
        try:
            self.config_manager = create_config_manager(config_path, enable_cache)
            self.config = self.config_manager.load_config()
            self.content_dir = self.config_manager.get_content_directory(self.config)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize document manager: {e}")
    
    def _generate_hash_id(self, url: str) -> str:
        """Generate secure hash ID from URL."""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()[:8]
    
    def _generate_filename(self, url: str) -> str:
        """Generate secure hash-based filename."""
        hash_id = self._generate_hash_id(url)
        filename = f"{hash_id}.md"
        return sanitize_filename(filename)
    
    def _save_config(self) -> None:
        """Save configuration with error handling."""
        try:
            self.config_manager.save_config(self.config)
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL with comprehensive security checks.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and safe
            
        Raises:
            ValidationError: If URL validation fails
            NetworkError: If network error occurs
        """
        try:
            return validate_url_sync(url)
        except Exception as e:
            if "SSRF" in str(e) or "private IP" in str(e):
                raise ValidationError(f"Security violation: {e}")
            raise NetworkError(f"URL validation failed: {e}")
    
    def add_doc(self, url: str, progress_callback: Optional[callable] = None) -> Optional[str]:
        """
        Download and add a document with security validation.
        
        Args:
            url: URL to download
            progress_callback: Optional progress callback
            
        Returns:
            Document hash ID if successful, None if failed
            
        Raises:
            ValidationError: If URL validation fails
            NetworkError: If network error occurs
            DownloadError: If download fails
        """
        print(f"Downloading {url}...")
        
        try:
            # Validate URL first
            self.validate_url(url)
            
            # Download content
            content = download_content_sync(url)
            
            if not content:
                raise DownloadError("Downloaded content is empty")
            
            # Generate secure filename
            hash_id = self._generate_hash_id(url)
            filename = self._generate_filename(url)
            file_path = self.content_dir / filename
            
            # Save content securely
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except OSError as e:
                raise DownloadError(f"Failed to save file: {e}")
            
            # Update metadata in config
            if "documents" not in self.config:
                self.config["documents"] = {}
            
            if hash_id not in self.config["documents"]:
                self.config["documents"][hash_id] = {
                    "url": url,
                    "name": None,
                    "description": None,
                    "tags": []
                }
            else:
                # Preserve existing metadata, just update URL
                self.config["documents"][hash_id]["url"] = url
            
            self._save_config()
            
            print(f"✓ Downloaded as {hash_id}.md")
            return hash_id
            
        except (ValidationError, NetworkError, DownloadError):
            print(f"✗ Failed to download {url}")
            raise
        except Exception as e:
            print(f"✗ Failed to download {url}")
            raise DownloadError(f"Unexpected error: {e}")
    
    async def add_doc_async(self, url: str, progress_callback: Optional[callable] = None) -> Optional[str]:
        """
        Asynchronously download and add a document.
        
        Args:
            url: URL to download
            progress_callback: Optional progress callback
            
        Returns:
            Document hash ID if successful, None if failed
            
        Raises:
            ValidationError: If URL validation fails
            NetworkError: If network error occurs
            DownloadError: If download fails
        """
        print(f"Downloading {url}...")
        
        try:
            # Download content asynchronously
            content = await download_content_async(url)
            
            if not content:
                raise DownloadError("Downloaded content is empty")
            
            # Generate secure filename
            hash_id = self._generate_hash_id(url)
            filename = self._generate_filename(url)
            file_path = self.content_dir / filename
            
            # Save content securely
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except OSError as e:
                raise DownloadError(f"Failed to save file: {e}")
            
            # Update metadata in config
            if "documents" not in self.config:
                self.config["documents"] = {}
            
            if hash_id not in self.config["documents"]:
                self.config["documents"][hash_id] = {
                    "url": url,
                    "name": None,
                    "description": None,
                    "tags": []
                }
            else:
                # Preserve existing metadata, just update URL
                self.config["documents"][hash_id]["url"] = url
            
            self._save_config()
            
            print(f"✓ Downloaded as {hash_id}.md")
            return hash_id
            
        except (ValidationError, NetworkError, DownloadError):
            print(f"✗ Failed to download {url}")
            raise
        except Exception as e:
            print(f"✗ Failed to download {url}")
            raise DownloadError(f"Unexpected error: {e}")
    
    def add_multiple(self, urls: List[str], use_async: bool = False) -> int:
        """
        Download multiple documents with progress tracking.
        
        Args:
            urls: List of URLs to download
            use_async: Whether to use async downloads
            
        Returns:
            Number of successfully downloaded documents
            
        Raises:
            ValidationError: If any URL validation fails critically
        """
        print(f"Downloading {len(urls)} documents...")
        
        if use_async:
            return asyncio.run(self._add_multiple_async(urls))
        else:
            return self._add_multiple_sync(urls)
    
    def _add_multiple_sync(self, urls: List[str]) -> int:
        """Synchronously download multiple documents."""
        success_count = 0
        for url in urls:
            try:
                if self.add_doc(url):
                    success_count += 1
            except Exception as e:
                print(f"Skipping {url}: {e}")
                continue
        
        print(f"\nCompleted: {success_count}/{len(urls)} documents downloaded")
        return success_count
    
    async def _add_multiple_async(self, urls: List[str]) -> int:
        """Asynchronously download multiple documents."""
        success_count = 0
        
        # Process downloads with concurrency limit
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent downloads
        
        async def download_with_semaphore(url):
            async with semaphore:
                try:
                    result = await self.add_doc_async(url)
                    return result is not None
                except Exception as e:
                    print(f"Skipping {url}: {e}")
                    return False
        
        # Run downloads concurrently
        results = await asyncio.gather(
            *[download_with_semaphore(url) for url in urls],
            return_exceptions=True
        )
        
        success_count = sum(1 for result in results if result is True)
        print(f"\nCompleted: {success_count}/{len(urls)} documents downloaded")
        return success_count
    
    def add_from_file(self, file_path: str, use_async: bool = False) -> int:
        """
        Download URLs from a file with validation.
        
        Args:
            file_path: Path to file containing URLs
            use_async: Whether to use async downloads
            
        Returns:
            Number of successfully downloaded documents
            
        Raises:
            ValidationError: If file cannot be read or contains invalid URLs
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise ValidationError(f"File not found: {file_path}")
            
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                urls = []
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Basic URL validation
                        if not (line.startswith('http://') or line.startswith('https://')):
                            print(f"Warning: Skipping invalid URL on line {line_num}: {line}")
                            continue
                        urls.append(line)
            
            if not urls:
                print(f"No valid URLs found in {file_path}")
                return 0
            
            return self.add_multiple(urls, use_async)
            
        except Exception as e:
            raise ValidationError(f"Error reading {file_path}: {e}")
    
    def set_metadata(self, hash_id: str, name: Optional[str] = None, 
                    description: Optional[str] = None, tags: Optional[str] = None) -> bool:
        """
        Set metadata for a document with validation.
        
        Args:
            hash_id: Document hash ID
            name: Document name
            description: Document description  
            tags: Comma-separated tags
            
        Returns:
            True if successful
            
        Raises:
            DocumentNotFoundError: If document not found
            ValidationError: If metadata validation fails
        """
        if "documents" not in self.config:
            self.config["documents"] = {}
        
        if hash_id not in self.config["documents"]:
            raise DocumentNotFoundError(f"Document '{hash_id}' not found")
        
        try:
            # Validate and sanitize metadata
            sanitized_name, sanitized_description = validate_document_metadata(name, description)
            
            # Update metadata
            if sanitized_name is not None:
                self.config["documents"][hash_id]["name"] = sanitized_name
            if sanitized_description is not None:
                self.config["documents"][hash_id]["description"] = sanitized_description
            if tags is not None:
                valid_tags = validate_and_clean_tags(tags)
                self.config["documents"][hash_id]["tags"] = valid_tags
            
            self._save_config()
            
            # Build update message
            updates = []
            if sanitized_name is not None:
                updates.append(f"name: '{sanitized_name}'")
            if sanitized_description is not None:
                updates.append(f"description: '{sanitized_description}'")
            if tags is not None:
                tag_list = self.config["documents"][hash_id]["tags"]
                if tag_list:
                    updates.append(f"tags: [{', '.join(tag_list)}]")
                else:
                    updates.append("tags: []")
            
            print(f"Updated {hash_id}: {', '.join(updates)}")
            return True
            
        except Exception as e:
            raise ValidationError(f"Failed to update metadata: {e}")
    
    def update_doc(self, hash_id: str, use_async: bool = False) -> bool:
        """
        Re-download a specific document.
        
        Args:
            hash_id: Document hash ID to update
            use_async: Whether to use async download
            
        Returns:
            True if successful
            
        Raises:
            DocumentNotFoundError: If document not found
            NetworkError: If download fails
        """
        if "documents" not in self.config or hash_id not in self.config["documents"]:
            raise DocumentNotFoundError(f"Document '{hash_id}' not found")
        
        url = self.config["documents"][hash_id]["url"]
        print(f"Updating {hash_id}...")
        
        try:
            if use_async:
                result = asyncio.run(self.add_doc_async(url))
            else:
                result = self.add_doc(url)
            
            if result:
                print(f"✓ {hash_id} updated")
                return True
            else:
                print(f"✗ {hash_id} update failed")
                return False
                
        except Exception as e:
            print(f"✗ {hash_id} update failed: {e}")
            raise
    
    def update_all(self, use_async: bool = False) -> int:
        """
        Update all documents.
        
        Args:
            use_async: Whether to use async downloads
            
        Returns:
            Number of successfully updated documents
        """
        if "documents" not in self.config or not self.config["documents"]:
            print("No documents to update")
            return 0
        
        docs = self.config["documents"]
        print(f"Updating {len(docs)} documents...")
        
        updated_count = 0
        
        if use_async:
            urls = [(hash_id, metadata["url"]) for hash_id, metadata in docs.items()]
            
            async def update_all_async():
                nonlocal updated_count
                semaphore = asyncio.Semaphore(3)  # Limit concurrent updates
                
                async def update_single(hash_id, url):
                    async with semaphore:
                        try:
                            result = await self.add_doc_async(url)
                            return result is not None
                        except Exception as e:
                            print(f"✗ {hash_id} update failed: {e}")
                            return False
                
                results = await asyncio.gather(
                    *[update_single(hash_id, url) for hash_id, url in urls],
                    return_exceptions=True
                )
                
                return sum(1 for result in results if result is True)
            
            updated_count = asyncio.run(update_all_async())
        else:
            for hash_id in docs.keys():
                try:
                    if self.update_doc(hash_id):
                        updated_count += 1
                except Exception as e:
                    print(f"Skipping {hash_id}: {e}")
                    continue
        
        print(f"\nCompleted: {updated_count}/{len(docs)} documents updated")
        return updated_count
    
    def remove_doc(self, hash_id: str) -> bool:
        """
        Remove a document with secure file deletion.
        
        Args:
            hash_id: Document hash ID to remove
            
        Returns:
            True if successful
            
        Raises:
            DocumentNotFoundError: If document not found
        """
        if "documents" not in self.config or hash_id not in self.config["documents"]:
            raise DocumentNotFoundError(f"Document '{hash_id}' not found")
        
        try:
            # Remove file securely
            filename = f"{hash_id}.md"
            file_path = self.content_dir / filename
            if file_path.exists():
                file_path.unlink()
            
            # Remove from config
            name = self.config["documents"][hash_id].get("name") or hash_id
            del self.config["documents"][hash_id]
            self._save_config()
            
            print(f"Removed '{name}' ({hash_id})")
            return True
            
        except Exception as e:
            raise LocalDocsError(f"Failed to remove document: {e}")
    
    def package_selected_docs(self, package_name: str, include_docs: List[str], 
                            format_type: str = 'toc', soft_links: bool = False) -> bool:
        """
        Package selected documents with security validation.
        
        Args:
            package_name: Name for the package directory
            include_docs: List of document IDs to include
            format_type: Package format ('toc', 'claude', 'json')
            soft_links: Whether to use soft links instead of copying files
            
        Returns:
            True if successful
            
        Raises:
            ValidationError: If package name is invalid
            PackagingError: If packaging fails
            DocumentNotFoundError: If documents not found
        """
        if "documents" not in self.config or not self.config["documents"]:
            print("No documents available for packaging")
            return True
        
        # Validate package name for security
        if not validate_package_name(package_name):
            raise ValidationError(
                f"Invalid package name '{package_name}'. "
                "Use only alphanumeric characters, hyphens, underscores, and dots."
            )
        
        # Filter documents to only include specified IDs
        all_docs = self.config["documents"]
        docs = {}
        missing_docs = []
        
        for doc_id in include_docs:
            if doc_id in all_docs:
                docs[doc_id] = all_docs[doc_id]
            else:
                missing_docs.append(doc_id)
        
        if missing_docs:
            print(f"Warning: Documents not found: {', '.join(missing_docs)}")
        
        if not docs:
            print("No valid documents to package")
            return False
        
        # Create package directory with security validation
        try:
            package_path = Path(package_name).resolve()
            
            # Security check: ensure package path is safe
            if package_path.exists():
                raise PackagingError(f"Directory '{package_name}' already exists")
            
            # Prevent path traversal
            if ".." in str(package_path) or str(package_path).startswith("/"):
                raise ValidationError("Invalid package path")
            
            package_path.mkdir(parents=True, mode=0o755)
            
        except (OSError, ValidationError) as e:
            raise PackagingError(f"Cannot create package directory: {e}")
        
        try:
            # Determine main file name based on format
            format_files = {
                'toc': 'index.md',
                'claude': 'claude-refs.md', 
                'json': 'data.json'
            }
            
            if format_type not in format_files:
                raise ValidationError(f"Unknown format: {format_type}")
            
            main_file = format_files[format_type]
            
            # Generate content based on format and mode
            if format_type == 'json':
                content = self._generate_json_format(docs, include_content=True)
            else:
                if soft_links:
                    content = self._generate_format_with_absolute_paths(docs, format_type)
                else:
                    content = self._generate_format_with_relative_paths(docs, format_type)
                    # Copy files when not using soft links
                    self._copy_files_to_package(docs, package_path)
                    # Create config file with only the exported documents
                    self._create_filtered_config(docs, package_path)
            
            # Write main file
            main_file_path = package_path / main_file
            with open(main_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if soft_links and format_type != 'json':
                print(f"Package '{package_name}' created with {main_file} (soft-links mode)")
            else:
                print(f"Package '{package_name}' created with {main_file}")
            
            return True
            
        except Exception as e:
            # Clean up on error
            if package_path.exists():
                shutil.rmtree(package_path, ignore_errors=True)
            raise PackagingError(f"Failed to create package: {e}")
    
    def package_all_docs(self, package_name: str, format_type: str = 'toc', 
                        soft_links: bool = False) -> bool:
        """
        Package all documents.
        
        Args:
            package_name: Name for the package directory
            format_type: Package format ('toc', 'claude', 'json')
            soft_links: Whether to use soft links instead of copying files
            
        Returns:
            True if successful
        """
        if "documents" not in self.config or not self.config["documents"]:
            print("No documents available for packaging")
            return True
        
        # Package all documents by passing all document IDs
        all_doc_ids = list(self.config["documents"].keys())
        return self.package_selected_docs(package_name, all_doc_ids, format_type, soft_links)
    
    def _generate_format_with_relative_paths(self, docs: Dict[str, Any], format_type: str) -> str:
        """Generate format with relative paths for package export."""
        if format_type == 'toc':
            lines = ["# Documentation Index", ""]
            for hash_id, metadata in docs.items():
                name = metadata.get("name") or f"Document {hash_id}"
                description = metadata.get("description") or "No description"
                filename = f"{hash_id}.md"
                lines.append(f"- [{name}]({filename}) - {description}")
            return "\n".join(lines)
        
        elif format_type == 'claude':
            lines = ["# Documentation References", ""]
            for hash_id, metadata in docs.items():
                name = metadata.get("name") or hash_id
                description = metadata.get("description") or f"{name} documentation"
                filename = f"{hash_id}.md"
                lines.append(f"See @{filename} for {description}.")
            return "\n".join(lines)
        
        return ""
    
    def _generate_format_with_absolute_paths(self, docs: Dict[str, Any], format_type: str) -> str:
        """Generate format with absolute paths for soft-links mode."""
        if format_type == 'toc':
            lines = ["# Documentation Index", ""]
            for hash_id, metadata in docs.items():
                name = metadata.get("name") or f"Document {hash_id}"
                description = metadata.get("description") or "No description"
                file_path = self.content_dir / f"{hash_id}.md"
                abs_path = str(file_path.resolve())
                lines.append(f"- [{name}]({abs_path}) - {description}")
            return "\n".join(lines)
        
        elif format_type == 'claude':
            lines = ["# Documentation References", ""]
            for hash_id, metadata in docs.items():
                name = metadata.get("name") or hash_id
                description = metadata.get("description") or f"{name} documentation"
                file_path = self.content_dir / f"{hash_id}.md"
                abs_path = str(file_path.resolve())
                lines.append(f"See @{abs_path} for {description}.")
            return "\n".join(lines)
        
        return ""
    
    def _generate_json_format(self, docs: Dict[str, Any], include_content: bool = False) -> str:
        """Generate JSON format export with optional content embedding."""
        export_data = {"documents": []}
        
        for hash_id, metadata in docs.items():
            doc_data = {
                "id": hash_id,
                "name": metadata.get("name"),
                "description": metadata.get("description"),
                "url": metadata.get("url"),
                "tags": metadata.get("tags", []),
                "file": f"{hash_id}.md"
            }
            
            if include_content:
                # Read and embed the actual content
                file_path = self.content_dir / f"{hash_id}.md"
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        doc_data["content"] = f.read()
                except Exception as e:
                    doc_data["content"] = f"Error reading file: {e}"
            
            export_data["documents"].append(doc_data)
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _copy_files_to_package(self, docs: Dict[str, Any], package_path: Path) -> None:
        """Copy markdown files to package directory with error handling."""
        for hash_id in docs.keys():
            source_file = self.content_dir / f"{hash_id}.md"
            dest_file = package_path / f"{hash_id}.md"
            
            if source_file.exists():
                try:
                    shutil.copy2(source_file, dest_file)
                except Exception as e:
                    print(f"Warning: Could not copy {hash_id}.md: {e}")
    
    def _create_filtered_config(self, docs: Dict[str, Any], package_path: Path) -> None:
        """Create config file with only the exported documents."""
        try:
            filtered_config = {
                "storage_directory": ".",
                "documents": docs
            }
            
            dest_config = package_path / "localdocs.config.json"
            with open(dest_config, 'w', encoding='utf-8') as f:
                json.dump(filtered_config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Could not create config file: {e}")
    
    def _filter_docs_by_tags(self, docs: Dict[str, Any], tag_filters: List[str]) -> Dict[str, Any]:
        """Filter documents by tags using OR logic."""
        if not tag_filters:
            return {}
        
        # If all available tags are selected, show all documents
        all_available_tags = set()
        for metadata in docs.values():
            all_available_tags.update(metadata.get("tags", []))
        
        if set(tag_filters) == all_available_tags:
            return docs
        
        filtered_docs = {}
        for hash_id, metadata in docs.items():
            doc_tags = metadata.get("tags", [])
            # Show document if it has ANY of the selected tags
            if any(tag in tag_filters for tag in doc_tags) or (not doc_tags and not tag_filters):
                filtered_docs[hash_id] = metadata
        
        return filtered_docs
    
    def extract_data(self, format_type: str = 'table', tag_filters: Optional[List[str]] = None,
                    fields: Optional[List[str]] = None, has_tags: Optional[bool] = None,
                    no_tags: bool = False, name_contains: Optional[str] = None,
                    desc_contains: Optional[str] = None, sort_by: str = 'id',
                    reverse: bool = False, limit: Optional[int] = None,
                    quiet: bool = False, count_only: bool = False,
                    output_file: Optional[str] = None) -> bool:
        """
        Extract data from documents with flexible filtering and formatting.
        
        This method provides comprehensive document data extraction with multiple
        filtering options, output formats, and security validation.
        
        Returns:
            True if successful
        """
        if "documents" not in self.config or not self.config["documents"]:
            if not quiet and not count_only:
                print("No documents found")
                print("Use 'localdocs add <url>' to add documents")
            return True
        
        try:
            docs = self.config["documents"]
            
            # Apply filtering
            if tag_filters:
                docs = self._filter_docs_by_tags(docs, tag_filters)
            
            if has_tags is True:
                docs = {k: v for k, v in docs.items() if v.get("tags", [])}
            elif no_tags:
                docs = {k: v for k, v in docs.items() if not v.get("tags", [])}
            
            if name_contains:
                docs = {k: v for k, v in docs.items()
                       if name_contains.lower() in (v.get("name") or "").lower()}
            
            if desc_contains:
                docs = {k: v for k, v in docs.items()
                       if desc_contains.lower() in (v.get("description") or "").lower()}
            
            # Handle count-only request
            if count_only:
                print(len(docs))
                return True
            
            if not docs:
                if not quiet:
                    print("No documents match the specified criteria")
                return True
            
            # Sort documents
            sort_functions = {
                'name': lambda x: x[1].get("name") or "",
                'url': lambda x: x[1].get("url") or "",
                'tags': lambda x: ",".join(x[1].get("tags", [])),
                'id': lambda x: x[0]
            }
            
            sort_key = sort_functions.get(sort_by, sort_functions['id'])
            sorted_items = sorted(docs.items(), key=sort_key, reverse=reverse)
            
            # Apply limit
            if limit:
                sorted_items = sorted_items[:limit]
            
            # Generate output
            output_content = self._generate_output(sorted_items, format_type, fields, quiet)
            
            # Output results
            if output_file:
                try:
                    output_path = Path(output_file)
                    # Security validation for output file
                    if ".." in str(output_path) or str(output_path).startswith("/"):
                        raise ValidationError("Invalid output file path")
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(output_content)
                    
                    if not quiet:
                        print(f"Output written to {output_file}")
                        
                except Exception as e:
                    print(f"Error writing to {output_file}: {e}")
                    return False
            else:
                print(output_content)
            
            return True
            
        except Exception as e:
            raise LocalDocsError(f"Data extraction failed: {e}")
    
    def _generate_output(self, sorted_items: List[Tuple[str, Dict[str, Any]]], 
                        format_type: str, fields: Optional[List[str]], quiet: bool) -> str:
        """Generate formatted output for document data."""
        all_fields = ['id', 'name', 'description', 'tags', 'url']
        selected_fields = [f for f in (fields or all_fields) if f in all_fields]
        
        if format_type == 'table':
            return self._generate_table_output(sorted_items, selected_fields, quiet)
        elif format_type == 'json':
            return self._generate_json_output(sorted_items, selected_fields)
        elif format_type == 'csv':
            return self._generate_csv_output(sorted_items, selected_fields, quiet)
        elif format_type == 'ids':
            return "\n".join(hash_id for hash_id, _ in sorted_items)
        else:
            raise ValidationError(f"Unknown output format: {format_type}")
    
    def _generate_table_output(self, sorted_items: List[Tuple[str, Dict[str, Any]]], 
                              selected_fields: List[str], quiet: bool) -> str:
        """Generate table format output."""
        lines = []
        
        if not quiet:
            headers = {'id': 'ID', 'name': 'Name', 'description': 'Description',
                      'tags': 'Tags', 'url': 'URL'}
            header_line = " ".join(f"{headers[f]:<20}" for f in selected_fields)
            lines.append(header_line)
            lines.append("-" * len(header_line))
        
        for hash_id, metadata in sorted_items:
            row_data = []
            for field in selected_fields:
                if field == 'id':
                    value = hash_id
                elif field == 'tags':
                    value = ",".join(metadata.get("tags", []))
                else:
                    value = metadata.get(field) or ""
                
                # Truncate for table display
                if len(value) > 18:
                    value = value[:15] + "..."
                row_data.append(f"{value:<20}")
            
            lines.append(" ".join(row_data))
        
        if not quiet:
            lines.append(f"\nTotal: {len(sorted_items)} documents")
        
        return "\n".join(lines)
    
    def _generate_json_output(self, sorted_items: List[Tuple[str, Dict[str, Any]]], 
                             selected_fields: List[str]) -> str:
        """Generate JSON format output."""
        data = []
        for hash_id, metadata in sorted_items:
            doc_data = {'id': hash_id}
            for field in selected_fields:
                if field == 'id':
                    continue  # Already added
                elif field == 'tags':
                    doc_data[field] = metadata.get("tags", [])
                else:
                    doc_data[field] = metadata.get(field)
            data.append(doc_data)
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _generate_csv_output(self, sorted_items: List[Tuple[str, Dict[str, Any]]], 
                            selected_fields: List[str], quiet: bool) -> str:
        """Generate CSV format output."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if not quiet:
            writer.writerow(selected_fields)
        
        for hash_id, metadata in sorted_items:
            row = []
            for field in selected_fields:
                if field == 'id':
                    row.append(hash_id)
                elif field == 'tags':
                    row.append(",".join(metadata.get("tags", [])))
                else:
                    row.append(metadata.get(field) or "")
            writer.writerow(row)
        
        return output.getvalue().strip()