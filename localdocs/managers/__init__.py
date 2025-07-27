"""
Manager modules for LocalDocs.

This package contains the core management classes for document handling
and interactive user interfaces.
"""

from .doc_manager import DocManager
from .interactive import InteractiveManager

__all__ = [
    'DocManager',
    'InteractiveManager'
]