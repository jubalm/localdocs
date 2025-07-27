"""
Interactive Manager for LocalDocs.

This module provides a secure, user-friendly terminal interface for managing
documents with keyboard navigation, filtering, and batch operations.
"""

from typing import Set, List, Tuple, Dict, Any, Optional, Union
from pathlib import Path

from ..exceptions import (
    LocalDocsError,
    ValidationError,
    InteractiveError,
    DocumentNotFoundError
)
from ..utils import (
    get_char,
    clear_screen,
    is_interactive_capable,
    get_terminal_size,
    render_controls,
    wrap_text,
    truncate_text,
    TerminalResizeDetector,
    validate_package_name,
    validate_document_metadata
)
from .doc_manager import DocManager


class InteractiveManager:
    """
    Interactive terminal interface for document management with security focus.
    
    This class provides a complete interactive experience for browsing,
    selecting, and managing documents with keyboard controls and visual feedback.
    """
    
    def __init__(self, doc_manager: DocManager) -> None:
        """
        Initialize interactive manager.
        
        Args:
            doc_manager: DocManager instance to use for operations
            
        Raises:
            InteractiveError: If interactive mode cannot be initialized
        """
        self.manager = doc_manager
        self.selected: Set[str] = set()  # Set of selected document hash_ids
        self.current_index = 0  # Current cursor position
        self.docs_list: List[Tuple[str, Dict[str, Any]]] = []  # Ordered list of (hash_id, metadata)
        self.resize_detector = TerminalResizeDetector()
        self.current_tag_filters: Set[str] = set()  # Set of active tag filters
        self.available_tags: Set[str] = set()  # All tags available in the collection
        self.in_filter_mode = False  # Whether we're in tag filter mode
    
    def _collect_available_tags(self) -> None:
        """Collect all unique tags from the document collection."""
        self.available_tags = set()
        if "documents" in self.manager.config:
            for metadata in self.manager.config["documents"].values():
                tags = metadata.get("tags", [])
                self.available_tags.update(tags)
    
    def _get_filtered_docs(self) -> Dict[str, Any]:
        """Get documents filtered by current tag filters."""
        all_docs = self.manager.config.get("documents", {})
        if not self.current_tag_filters:
            return all_docs
        return self.manager._filter_docs_by_tags(all_docs, list(self.current_tag_filters))
    
    def _update_docs_list(self) -> None:
        """Update the docs list with current filtering and clean up invalid selections."""
        filtered_docs = self._get_filtered_docs()
        self.docs_list = list(filtered_docs.items())
        
        # Clean up selections - remove documents that are no longer visible
        visible_doc_ids = set(filtered_docs.keys())
        self.selected = self.selected.intersection(visible_doc_ids)
        
        # Adjust current index if needed
        if self.docs_list:
            self.current_index = min(self.current_index, len(self.docs_list) - 1)
        else:
            self.current_index = 0
    
    def run(self) -> bool:
        """
        Main interactive loop with comprehensive error handling.
        
        Returns:
            True if successful, False if failed to start
            
        Raises:
            InteractiveError: If interactive mode fails
        """
        try:
            if not is_interactive_capable():
                print("Interactive mode requires a terminal that supports keyboard input.")
                print("Use regular CLI commands instead:")
                print("  localdocs extract  - Extract document data")
                print("  localdocs package  - Create document packages")
                print("  localdocs remove   - Remove a document")
                return False
            
            # Load documents
            if "documents" not in self.manager.config or not self.manager.config["documents"]:
                print("No documents found. Use 'localdocs add <url>' to add documents first.")
                return True
            
            # Initialize tag filtering system
            self._collect_available_tags()
            self.current_tag_filters = self.available_tags.copy()  # Start with all tags selected
            self.current_index = 0
            self.selected = set()
            self._update_docs_list()
            
            # Initial render
            self._render_interface()
            
            # Main input loop
            while True:
                try:
                    key = get_char()
                    
                    if not self._handle_key(key):
                        break  # User chose to quit
                    
                    # Re-render after key action
                    self._render_interface()
                        
                except KeyboardInterrupt:
                    clear_screen()
                    print("Interactive mode cancelled.")
                    break
                except Exception as e:
                    self._show_error_message(f"Error handling input: {e}")
            
            return True
            
        except Exception as e:
            raise InteractiveError(f"Interactive mode failed: {e}")
    
    def _render_interface(self) -> None:
        """Render the main interface with responsive layout."""
        try:
            clear_screen()
            
            print("LocalDocs - Document Manager")
            print("=" * 50)
            print()
            
            # Get terminal size for layout decisions
            width, height = get_terminal_size()
            
            # Render documents with appropriate layout
            if width < 60:  # MIN_TERMINAL_WIDTH
                self._render_tree_layout(width)
            else:
                self._render_column_layout(width)
            
            # Status and controls
            print()
            self._render_status_line()
            print()
            self._render_control_instructions(width)
            
        except Exception as e:
            print(f"Error rendering interface: {e}")
    
    def _render_tree_layout(self, width: int) -> None:
        """Render documents in tree layout for narrow terminals."""
        for i, (hash_id, metadata) in enumerate(self.docs_list):
            # Current document indicator
            cursor = ">" if i == self.current_index else " "
            
            # Selection checkbox
            checkbox = "[x]" if hash_id in self.selected else "[ ]"
            
            # Document info
            name = metadata.get("name") or "[unnamed]"
            description = metadata.get("description") or "[no description]"
            tags = metadata.get("tags", [])
            
            # Main line: cursor + checkbox + hash_id
            print(f"{cursor} {checkbox} {hash_id}")
            
            # Tree branches: name, tags, and description with indentation
            print(f"     ├─ {truncate_text(name, width - 8)}")
            if tags:
                tags_str = ",".join(tags)
                print(f"     ├─ tags: {truncate_text(tags_str, width - 15)}")
            
            # Handle long descriptions by wrapping
            desc_lines = wrap_text(description, width - 8, "        ")
            for j, line in enumerate(desc_lines):
                if j == 0:
                    print(f"     └─ {line}")
                else:
                    print(f"        {line}")
            
            # Add spacing between documents
            if i < len(self.docs_list) - 1:
                print()
    
    def _render_column_layout(self, width: int) -> None:
        """Render documents in column layout for wide terminals."""
        # Calculate optimal column widths
        fixed_width = 8  # cursor (1) + space (1) + checkbox (3) + spaces (3)
        id_width = 10
        remaining_width = width - fixed_width - id_width
        
        if remaining_width > 20:
            # Calculate name column width based on content
            max_name_length = 0
            for _, metadata in self.docs_list:
                name = metadata.get("name") or "[unnamed]"
                max_name_length = max(max_name_length, len(name))
            
            name_width = min(max_name_length + 2, remaining_width // 2, 40)
            name_width = max(name_width, 10)
            desc_width = max(10, remaining_width - name_width)
        else:
            name_width = 10
            desc_width = max(10, remaining_width - name_width)
        
        # Render documents
        for i, (hash_id, metadata) in enumerate(self.docs_list):
            cursor = ">" if i == self.current_index else " "
            checkbox = "[x]" if hash_id in self.selected else "[ ]"
            
            name = metadata.get("name") or "[unnamed]"
            description = metadata.get("description") or "[no description]"
            
            # Truncate to fit column widths
            name = truncate_text(name, name_width)
            description = truncate_text(description, desc_width)
            
            print(f"{cursor} {checkbox} {hash_id:<{id_width}} {name:<{name_width}} {description}")
    
    def _render_status_line(self) -> None:
        """Render status information line."""
        total_docs = len(self.manager.config.get("documents", {}))
        
        if self.current_tag_filters:
            # Show filtered status
            tag_list = sorted(list(self.current_tag_filters))
            if len(tag_list) <= 3:
                tags_str = ", ".join(tag_list)
            else:
                tags_str = f"{', '.join(tag_list[:3])}, +{len(tag_list)-3} more"
            print(f"Selected: {len(self.selected)}/{len(self.docs_list)} documents tagged {tags_str}")
        else:
            print(f"Selected: {len(self.selected)}/{len(self.docs_list)} documents")
    
    def _render_control_instructions(self, width: int) -> None:
        """Render control instructions optimized for terminal width."""
        # Define control sets
        extended_controls = [
            "[j/k] Navigate", "[Space] Toggle selection", "[a] Select/deselect all",
            "[f] Filters", "[d] Delete", "[x] Package", "[u] Update selected",
            "[s] Set metadata", "[q] Quit"
        ]
        
        shorthand_controls = [
            "[j/k] Nav", "[Space] Select", "[a] All", "[f] Filters",
            "[d] Delete", "[x] Package", "[u] Update", "[s] Set", "[q] Quit"
        ]
        
        # Choose appropriate control set based on width
        if width >= 120:
            render_controls(extended_controls, width)
        else:
            render_controls(shorthand_controls, width)
    
    def _handle_key(self, key: str) -> bool:
        """
        Handle keyboard input with comprehensive error handling.
        
        Args:
            key: Key pressed by user
            
        Returns:
            False to quit, True to continue
        """
        try:
            if key in ('q', 'Q'):
                return self._handle_quit_confirmation()
            
            elif key in ('j',):  # Down navigation
                if self.docs_list and self.current_index < len(self.docs_list) - 1:
                    self.current_index += 1
            
            elif key in ('k',):  # Up navigation
                if self.docs_list and self.current_index > 0:
                    self.current_index -= 1
            
            elif key == '\x1b':  # Escape sequence (arrow keys)
                self._handle_arrow_keys()
            
            elif key == ' ':  # Toggle selection
                self._handle_toggle_selection()
            
            elif key in ('a', 'A'):  # Select/deselect all
                self._handle_toggle_all_selection()
            
            elif key in ('d', 'D'):  # Delete selected
                self._handle_delete_operation()
            
            elif key in ('x', 'X'):  # Package selected
                self._handle_package_operation()
            
            elif key in ('u', 'U'):  # Update selected
                self._handle_update_operation()
            
            elif key in ('s', 'S'):  # Set metadata
                self._handle_metadata_operation()
            
            elif key in ('f', 'F'):  # Filter by tags
                self._handle_tag_filter_mode()
            
            return True
            
        except Exception as e:
            self._show_error_message(f"Error processing command: {e}")
            return True
    
    def _handle_arrow_keys(self) -> None:
        """Handle arrow key sequences."""
        try:
            next_char = get_char()
            if next_char == '[':
                arrow_key = get_char()
                if arrow_key == 'A' and self.docs_list and self.current_index > 0:  # Up
                    self.current_index -= 1
                elif arrow_key == 'B' and self.docs_list and self.current_index < len(self.docs_list) - 1:  # Down
                    self.current_index += 1
        except Exception:
            pass  # Ignore arrow key errors
    
    def _handle_toggle_selection(self) -> None:
        """Handle toggling selection of current document."""
        if self.docs_list:
            current_hash_id = self.docs_list[self.current_index][0]
            if current_hash_id in self.selected:
                self.selected.remove(current_hash_id)
            else:
                self.selected.add(current_hash_id)
    
    def _handle_toggle_all_selection(self) -> None:
        """Handle smart select/deselect all operation."""
        all_hash_ids = {hash_id for hash_id, _ in self.docs_list}
        if len(self.selected) == len(all_hash_ids):
            # All selected - deselect all
            self.selected.clear()
        else:
            # Some or none selected - select all
            self.selected = all_hash_ids.copy()
    
    def _handle_delete_operation(self) -> None:
        """Handle delete operation with confirmation."""
        if not self.selected:
            self._show_message("No documents selected for deletion.")
            return
        
        try:
            clear_screen()
            print("Delete the following documents?")
            print()
            
            # Show what will be deleted
            for hash_id in self.selected:
                metadata = self.manager.config["documents"][hash_id]
                name = metadata.get("name") or "[unnamed]"
                print(f"- {hash_id} ({name})")
            
            print()
            print("This cannot be undone.")
            response = input("Continue? [y/N]: ").strip().lower()
            
            if response in ('y', 'yes'):
                # Perform deletions
                deleted_count = 0
                failed_deletions = []
                
                for hash_id in list(self.selected):
                    try:
                        if self.manager.remove_doc(hash_id):
                            deleted_count += 1
                    except Exception as e:
                        failed_deletions.append(f"{hash_id}: {e}")
                
                # Refresh docs list and clear selection
                self._update_docs_list()
                self.selected.clear()
                if self.docs_list:
                    self.current_index = min(self.current_index, len(self.docs_list) - 1)
                else:
                    self.current_index = 0
                
                message = f"Deleted {deleted_count} documents."
                if failed_deletions:
                    message += f" Failed: {len(failed_deletions)}"
                
                self._show_message(message)
            else:
                self._show_message("Deletion cancelled.")
                
        except Exception as e:
            self._show_error_message(f"Delete operation failed: {e}")
    
    def _handle_package_operation(self) -> None:
        """Handle package creation with validation."""
        if not self.selected:
            self._show_message("No documents selected for packaging.")
            return
        
        try:
            clear_screen()
            print("Package the following documents?")
            print()
            
            # Show what will be packaged
            for hash_id in self.selected:
                metadata = self.manager.config["documents"][hash_id]
                name = metadata.get("name") or "[unnamed]"
                print(f"- {hash_id} ({name})")
            
            print()
            
            # Get package name with validation
            while True:
                package_name = input("Package name: ").strip()
                if not package_name:
                    self._show_message("Package cancelled - no package name provided.")
                    return
                
                if validate_package_name(package_name):
                    break
                else:
                    print("Invalid package name. Use only alphanumeric characters, hyphens, underscores, and dots.")
                    print()
            
            # Get format
            format_choice = input("Format [toc/claude/json] (default: toc): ").strip().lower()
            if format_choice not in ('toc', 'claude', 'json'):
                format_choice = 'toc'
            
            # Confirm operation
            response = input(f"Create package '{package_name}'? [Y/n]: ").strip().lower()
            
            if response in ('', 'y', 'yes'):
                selected_doc_ids = list(self.selected)
                success = self.manager.package_selected_docs(package_name, selected_doc_ids, format_choice, False)
                
                if success:
                    self._show_message(f"Package '{package_name}' created successfully.")
                else:
                    self._show_error_message("Package creation failed.")
            else:
                self._show_message("Package creation cancelled.")
                
        except Exception as e:
            self._show_error_message(f"Package operation failed: {e}")
    
    def _handle_update_operation(self) -> None:
        """Handle update operation with progress feedback."""
        if not self.selected:
            self._show_message("No documents selected for update.")
            return
        
        try:
            clear_screen()
            print("Update the following documents from their URLs?")
            print()
            
            # Show what will be updated
            for hash_id in self.selected:
                metadata = self.manager.config["documents"][hash_id]
                name = metadata.get("name") or "[unnamed]"
                print(f"- {hash_id} ({name})")
            
            print()
            print("This will re-download content from the original URLs.")
            response = input("Continue? [Y/n]: ").strip().lower()
            
            if response in ('', 'y', 'yes'):
                updated_count = 0
                failed_updates = []
                
                for hash_id in self.selected:
                    try:
                        if self.manager.update_doc(hash_id):
                            updated_count += 1
                    except Exception as e:
                        failed_updates.append(f"{hash_id}: {e}")
                
                message = f"Updated {updated_count}/{len(self.selected)} documents."
                if failed_updates:
                    message += f" Failed: {len(failed_updates)}"
                
                self._show_message(message)
            else:
                self._show_message("Update cancelled.")
                
        except Exception as e:
            self._show_error_message(f"Update operation failed: {e}")
    
    def _handle_metadata_operation(self) -> None:
        """Handle setting metadata for current document."""
        if not self.docs_list:
            return
        
        try:
            current_hash_id = self.docs_list[self.current_index][0]
            metadata = self.manager.config["documents"][current_hash_id]
            
            clear_screen()
            print(f"Edit metadata for {current_hash_id}:")
            print()
            
            # Get current values
            current_name = metadata.get("name") or ""
            current_desc = metadata.get("description") or ""
            current_tags = ",".join(metadata.get("tags", []))
            
            # Prompt for new values
            print(f"Name (current: {current_name or '[unnamed]'}): ", end="")
            new_name = input().strip()
            
            print(f"Description (current: {current_desc or '[no description]'}): ", end="")
            new_description = input().strip()
            
            print(f"Tags (current: {current_tags or '[no tags]'}): ", end="")
            new_tags = input().strip()
            
            # Use current values if nothing entered
            final_name = new_name if new_name else current_name
            final_desc = new_description if new_description else current_desc
            final_tags = new_tags if new_tags else current_tags
            
            # Update metadata
            self.manager.set_metadata(
                current_hash_id,
                final_name if final_name != current_name else None,
                final_desc if final_desc != current_desc else None,
                final_tags if final_tags != current_tags else None
            )
            
            # Refresh data
            self._collect_available_tags()
            self._update_docs_list()
            
            self._show_message(f"Updated metadata for {current_hash_id}.")
            
        except Exception as e:
            self._show_error_message(f"Metadata update failed: {e}")
    
    def _handle_tag_filter_mode(self) -> None:
        """Handle tag filter mode interface."""
        if not self.available_tags:
            self._show_message("No tags available in the collection.")
            return
        
        try:
            available_tags_list = sorted(list(self.available_tags))
            current_tag_index = 0
            
            while True:
                clear_screen()
                
                # Calculate filtered doc count
                temp_filtered = self._get_filtered_docs()
                filtered_count = len(temp_filtered)
                total_count = len(self.manager.config.get("documents", {}))
                
                print("Filter by tags:")
                print()
                
                # Display tags with checkboxes
                for i, tag in enumerate(available_tags_list):
                    cursor = ">" if i == current_tag_index else " "
                    checkbox = "[x]" if tag in self.current_tag_filters else "[ ]"
                    print(f"{cursor} {checkbox} {tag}")
                
                print()
                print(f"{filtered_count} documents match current filters (Total: {total_count})")
                print()
                print("[j/k/↕] navigate  [space] toggle  [a] toggle all  [enter/esc] back to documents")
                
                key = get_char()
                
                if key in ('j',) and current_tag_index < len(available_tags_list) - 1:
                    current_tag_index += 1
                elif key in ('k',) and current_tag_index > 0:
                    current_tag_index -= 1
                elif key == '\x1b':  # Handle escape and arrow keys
                    arrow_handled = self._handle_filter_mode_arrows(available_tags_list, current_tag_index)
                    if isinstance(arrow_handled, int):
                        current_tag_index = arrow_handled
                    elif not arrow_handled:
                        break  # Exit on plain escape
                elif key == ' ' and available_tags_list:
                    # Toggle current tag
                    current_tag = available_tags_list[current_tag_index]
                    if current_tag in self.current_tag_filters:
                        self.current_tag_filters.remove(current_tag)
                    else:
                        self.current_tag_filters.add(current_tag)
                    self._update_docs_list()
                elif key in ('a', 'A'):
                    # Smart toggle all
                    if len(self.current_tag_filters) == len(self.available_tags):
                        self.current_tag_filters.clear()
                    else:
                        self.current_tag_filters = self.available_tags.copy()
                    self._update_docs_list()
                elif key in ('\r', '\n'):  # Enter to exit
                    break
                    
        except Exception as e:
            self._show_error_message(f"Tag filter mode failed: {e}")
    
    def _handle_filter_mode_arrows(self, available_tags_list: List[str], current_index: int) -> Union[int, bool]:
        """Handle arrow keys in filter mode."""
        try:
            next_char = get_char()
            if next_char == '[':
                arrow_key = get_char()
                if arrow_key == 'A':  # Up arrow
                    return max(0, current_index - 1)
                elif arrow_key == 'B':  # Down arrow
                    return min(len(available_tags_list) - 1, current_index + 1)
                elif arrow_key in ('C', 'D'):  # Left/Right arrows
                    return True  # Handled but ignored
            return False  # Not an arrow sequence, treat as exit
        except Exception:
            return False
    
    def _handle_quit_confirmation(self) -> bool:
        """
        Handle quit confirmation with context awareness.
        
        Returns:
            False to quit, True to stay
        """
        try:
            clear_screen()
            
            # Show context-aware message
            if self.selected:
                print(f"You have {len(self.selected)} document{'s' if len(self.selected) != 1 else ''} selected.")
            
            print("Exit interactive manager?")
            print()
            print("[y] Yes, exit    [n] No, stay")
            
            while True:
                key = get_char().lower()
                
                if key == 'y':
                    return False  # Quit
                elif key == 'n':
                    return True   # Stay
                # Ignore other keys
                
        except Exception as e:
            self._show_error_message(f"Quit confirmation failed: {e}")
            return False  # Default to quit on error
    
    def _show_message(self, message: str) -> None:
        """Show a message and wait for keypress."""
        try:
            clear_screen()
            print(message)
            print()
            print("Press any key to continue...")
            get_char()
        except Exception:
            pass  # Ignore errors in message display
    
    def _show_error_message(self, message: str) -> None:
        """Show an error message with appropriate formatting."""
        try:
            clear_screen()
            print("Error:")
            print(message)
            print()
            print("Press any key to continue...")
            get_char()
        except Exception:
            pass  # Ignore errors in error display