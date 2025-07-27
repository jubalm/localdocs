"""
Configuration management utilities for LocalDocs.

This module provides secure configuration loading, saving, and caching
with path validation and migration support.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .validation import validate_config_path, PathTraversalError, ValidationError


@dataclass
class DocumentMetadata:
    """Document metadata structure with validation."""
    url: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ConfigCache:
    """Thread-safe configuration cache with TTL support."""
    
    def __init__(self, ttl_seconds: int = 60):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
    
    def get(self, config_path: str) -> Optional[Dict[str, Any]]:
        """Get cached config if still valid."""
        if config_path not in self._cache:
            return None
        
        # Check if cache is expired
        if time.time() - self._timestamps[config_path] > self.ttl_seconds:
            self._invalidate(config_path)
            return None
        
        return self._cache[config_path].copy()
    
    def set(self, config_path: str, config: Dict[str, Any]) -> None:
        """Cache config with current timestamp."""
        self._cache[config_path] = config.copy()
        self._timestamps[config_path] = time.time()
    
    def _invalidate(self, config_path: str) -> None:
        """Remove config from cache."""
        self._cache.pop(config_path, None)
        self._timestamps.pop(config_path, None)
    
    def clear(self) -> None:
        """Clear all cached configs."""
        self._cache.clear()
        self._timestamps.clear()


# Global config cache instance
_config_cache = ConfigCache()


class ConfigManager:
    """Secure configuration manager with validation and caching."""
    
    def __init__(self, config_path: Optional[Path] = None, enable_cache: bool = True):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Explicit config path, or None for auto-discovery
            enable_cache: Whether to enable configuration caching
        """
        self.enable_cache = enable_cache
        
        if config_path is None:
            self.config_path = self._discover_config_path()
        else:
            self.config_path = validate_config_path(config_path)
        
        self.base_dir = self.config_path.parent
        self._ensure_directories()
    
    def _discover_config_path(self) -> Path:
        """
        Secure two-level config discovery.
        
        Returns:
            Validated config path
            
        Raises:
            PathTraversalError: If path traversal attempt detected
            ValidationError: If no valid config path found
        """
        try:
            # 1. Check current working directory
            cwd_config = Path.cwd() / "localdocs.config.json"
            if cwd_config.exists():
                return validate_config_path(cwd_config)
            
            # 2. Fallback to user home directory
            home_config = Path.home() / ".localdocs" / "localdocs.config.json"
            return validate_config_path(home_config)
            
        except (OSError, PathTraversalError) as e:
            raise ValidationError(f"Config path discovery failed: {e}")
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist with proper permissions."""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
        except OSError as e:
            raise ValidationError(f"Cannot create config directory: {e}")
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration with caching and validation.
        
        Returns:
            Configuration dictionary
            
        Raises:
            ValidationError: If config loading fails
        """
        config_path_str = str(self.config_path)
        
        # Check cache first
        if self.enable_cache:
            cached_config = _config_cache.get(config_path_str)
            if cached_config is not None:
                return cached_config
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Validate config structure
                config = self._validate_and_migrate_config(config)
            else:
                config = self._create_default_config()
            
            # Cache the loaded config
            if self.enable_cache:
                _config_cache.set(config_path_str, config)
            
            return config
            
        except (json.JSONDecodeError, OSError) as e:
            raise ValidationError(f"Failed to load config from {self.config_path}: {e}")
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration with validation.
        
        Args:
            config: Configuration dictionary to save
            
        Raises:
            ValidationError: If config saving fails
        """
        try:
            # Validate config before saving
            validated_config = self._validate_config_structure(config)
            
            # Ensure directory exists
            self._ensure_directories()
            
            # Write config atomically
            temp_path = self.config_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(validated_config, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_path.replace(self.config_path)
            
            # Update cache
            if self.enable_cache:
                _config_cache.set(str(self.config_path), validated_config)
                
        except (OSError, json.JSONEncodeError) as e:
            raise ValidationError(f"Failed to save config to {self.config_path}: {e}")
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        return {
            "storage_directory": ".",
            "documents": {}
        }
    
    def _validate_and_migrate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and migrate configuration from older versions.
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            Validated and migrated configuration
        """
        # Clean up deprecated fields
        deprecated_fields = ["max_keep_versions"]
        for field in deprecated_fields:
            config.pop(field, None)
        
        # Migrate documents to include tags field
        if "documents" in config:
            for hash_id, metadata in config["documents"].items():
                if "tags" not in metadata:
                    metadata["tags"] = []
                
                # Validate document metadata
                if not isinstance(metadata.get("tags"), list):
                    metadata["tags"] = []
        
        return self._validate_config_structure(config)
    
    def _validate_config_structure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration structure and sanitize values.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Validated configuration
            
        Raises:
            ValidationError: If config structure is invalid
        """
        if not isinstance(config, dict):
            raise ValidationError("Config must be a dictionary")
        
        # Ensure required fields exist
        if "storage_directory" not in config:
            config["storage_directory"] = "."
        
        if "documents" not in config:
            config["documents"] = {}
        
        # Validate storage_directory
        storage_dir = config["storage_directory"]
        if not isinstance(storage_dir, str):
            raise ValidationError("storage_directory must be a string")
        
        # Validate documents structure
        documents = config["documents"]
        if not isinstance(documents, dict):
            raise ValidationError("documents must be a dictionary")
        
        # Validate each document entry
        for hash_id, metadata in documents.items():
            if not isinstance(hash_id, str) or len(hash_id) != 8:
                raise ValidationError(f"Invalid document hash ID: {hash_id}")
            
            if not isinstance(metadata, dict):
                raise ValidationError(f"Document metadata must be a dictionary: {hash_id}")
            
            # Validate required fields
            if "url" not in metadata:
                raise ValidationError(f"Document missing URL: {hash_id}")
            
            # Ensure optional fields are properly typed
            if "name" in metadata and metadata["name"] is not None:
                if not isinstance(metadata["name"], str):
                    metadata["name"] = str(metadata["name"])
            
            if "description" in metadata and metadata["description"] is not None:
                if not isinstance(metadata["description"], str):
                    metadata["description"] = str(metadata["description"])
            
            if "tags" not in metadata:
                metadata["tags"] = []
            elif not isinstance(metadata["tags"], list):
                metadata["tags"] = []
            else:
                # Validate tags
                metadata["tags"] = [tag for tag in metadata["tags"] 
                                 if isinstance(tag, str) and len(tag) <= 20]
        
        return config
    
    def get_content_directory(self, config: Dict[str, Any]) -> Path:
        """
        Get content directory path with validation.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Validated content directory path
            
        Raises:
            ValidationError: If content directory is invalid
        """
        storage_dir = config.get("storage_directory", ".")
        
        if storage_dir == ".":
            content_dir = self.base_dir
        else:
            # Validate storage directory for path traversal
            if ".." in storage_dir or storage_dir.startswith("/"):
                raise ValidationError(f"Invalid storage directory: {storage_dir}")
            
            content_dir = self.base_dir / storage_dir
        
        try:
            content_dir.mkdir(exist_ok=True, mode=0o755)
            return content_dir
        except OSError as e:
            raise ValidationError(f"Cannot create content directory: {e}")
    
    def invalidate_cache(self) -> None:
        """Invalidate cached configuration."""
        if self.enable_cache:
            _config_cache.clear()


def create_config_manager(config_path: Optional[str] = None, 
                         enable_cache: bool = True) -> ConfigManager:
    """
    Factory function to create a configuration manager.
    
    Args:
        config_path: Optional explicit config path
        enable_cache: Whether to enable configuration caching
        
    Returns:
        ConfigManager instance
    """
    path_obj = Path(config_path) if config_path else None
    return ConfigManager(path_obj, enable_cache)