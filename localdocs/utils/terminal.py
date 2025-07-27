"""
Terminal control utilities for LocalDocs interactive mode.

This module provides cross-platform terminal control functions for
keyboard input, screen management, and layout calculations.
"""

import sys
import shutil
from typing import List, Tuple, Optional


# Terminal layout constants
MIN_TERMINAL_WIDTH = 60
DEFAULT_TERMINAL_WIDTH = 80
MIN_SPACING = 4
HORIZONTAL_PADDING = 4
MAX_NAME_COLUMN_WIDTH = 40
MIN_COLUMN_WIDTH = 8


def get_char() -> str:
    """
    Get single character input without pressing Enter.
    
    Returns:
        Single character from user input
    """
    try:
        # Unix/Linux/macOS
        import termios
        import tty
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char
        
    except ImportError:
        # Windows fallback - use msvcrt if available
        try:
            import msvcrt
            return msvcrt.getch().decode('utf-8')
        except (ImportError, UnicodeDecodeError):
            # Ultimate fallback - regular input
            user_input = input("Press Enter after your choice: ")
            return user_input[0] if user_input else ''


def clear_screen() -> None:
    """Clear the terminal screen using ANSI escape sequences."""
    print("\033[2J\033[H", end="")


def is_interactive_capable() -> bool:
    """
    Check if terminal supports interactive features.
    
    Returns:
        True if terminal supports interactive mode, False otherwise
    """
    return sys.stdin.isatty() and sys.stdout.isatty()


def get_terminal_size() -> Tuple[int, int]:
    """
    Get current terminal size with fallback.
    
    Returns:
        Tuple of (width, height)
    """
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except (AttributeError, OSError):
        return DEFAULT_TERMINAL_WIDTH, 24


def build_centered_line(items: List[str], available_width: int) -> str:
    """
    Build a line of controls using centered cells.
    
    Args:
        items: List of text items to center
        available_width: Total width available for centering
        
    Returns:
        Centered line as string
    """
    if not items:
        return ""
    
    num_cols = len(items)
    col_width = available_width // num_cols
    
    # Build centered columns
    cells = []
    for item in items:
        padding = (col_width - len(item)) // 2
        cell = f"{' ' * padding}{item}{' ' * (col_width - padding - len(item))}"
        cells.append(cell)
    
    return ''.join(cells)


def render_controls(controls: List[str], width: int) -> None:
    """
    Render control instructions optimized for terminal width.
    
    Args:
        controls: List of control strings to display
        width: Available terminal width
    """
    if not controls:
        return
    
    min_spacing = MIN_SPACING
    horizontal_padding = HORIZONTAL_PADDING
    
    # Calculate space requirements
    total_content = sum(len(control) for control in controls)
    required_width = total_content + (len(controls) - 1) * min_spacing + horizontal_padding
    
    if required_width <= width:
        # Controls fit on one line - use natural even spacing with padding
        available_space = width - sum(len(c) for c in controls) - horizontal_padding
        spaces_between = available_space // (len(controls) - 1) if len(controls) > 1 else 0
        spaces_between = max(spaces_between, min_spacing)
        
        line = "  "  # Left padding
        for i, control in enumerate(controls):
            line += control
            if i < len(controls) - 1:  # Not the last control
                line += " " * spaces_between
        line += "  "  # Right padding
        print(line)
    else:
        # Use 2-column centered layout
        mid = len(controls) // 2
        line1 = controls[:mid]
        line2 = controls[mid:]
        if line1:
            print(build_centered_line(line1, width))
        if line2:
            print(build_centered_line(line2, width))


def wrap_text(text: str, width: int, indent: str = "") -> List[str]:
    """
    Wrap text to fit within specified width.
    
    Args:
        text: Text to wrap
        width: Maximum width for each line
        indent: Indentation for continuation lines
        
    Returns:
        List of wrapped lines
    """
    if not text or width <= 0:
        return []
    
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        # Check if adding this word would exceed width
        test_line = current_line + (" " + word if current_line else word)
        if len(test_line) <= width:
            current_line = test_line
        else:
            # Current line is full, start new line
            if current_line:
                lines.append(current_line)
            current_line = word
    
    # Add the last line if it exists
    if current_line:
        lines.append(current_line)
    
    # Add indentation to continuation lines
    if indent and len(lines) > 1:
        lines = [lines[0]] + [indent + line for line in lines[1:]]
    
    return lines


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to fit within maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    if max_length <= len(suffix):
        return suffix[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


def calculate_column_widths(data: List[dict], terminal_width: int, 
                          fixed_columns: dict, flexible_columns: List[str]) -> dict:
    """
    Calculate optimal column widths for tabular display.
    
    Args:
        data: List of data dictionaries
        terminal_width: Available terminal width
        fixed_columns: Dict of {column_name: width} for fixed-width columns
        flexible_columns: List of column names that can be resized
        
    Returns:
        Dict of {column_name: width} for all columns
    """
    if not data or not flexible_columns:
        return fixed_columns.copy()
    
    # Calculate remaining width after fixed columns and spacing
    fixed_width = sum(fixed_columns.values())
    spacing = len(fixed_columns) + len(flexible_columns) - 1  # Spaces between columns
    available_width = terminal_width - fixed_width - spacing
    
    if available_width <= 0:
        # Not enough space, use minimum widths
        result = fixed_columns.copy()
        min_width = MIN_COLUMN_WIDTH
        for col in flexible_columns:
            result[col] = min_width
        return result
    
    # Calculate optimal widths for flexible columns
    result = fixed_columns.copy()
    
    # Find maximum content length for each flexible column
    max_lengths = {}
    for col in flexible_columns:
        max_length = 0
        for item in data:
            content = str(item.get(col, ""))
            max_length = max(max_length, len(content))
        max_lengths[col] = max(max_length, MIN_COLUMN_WIDTH)
    
    # Distribute available width proportionally
    total_desired = sum(max_lengths.values())
    
    if total_desired <= available_width:
        # All columns fit at their desired width
        result.update(max_lengths)
    else:
        # Scale down proportionally
        for col in flexible_columns:
            desired = max_lengths[col]
            proportion = desired / total_desired
            allocated = max(int(available_width * proportion), MIN_COLUMN_WIDTH)
            result[col] = allocated
    
    return result


class TerminalResizeDetector:
    """Utility class to detect terminal resize events."""
    
    def __init__(self):
        self.last_size: Optional[Tuple[int, int]] = None
    
    def check_resize(self) -> bool:
        """
        Check if terminal has been resized.
        
        Returns:
            True if terminal size changed, False otherwise
        """
        current_size = get_terminal_size()
        if self.last_size != current_size:
            self.last_size = current_size
            return True
        return False
    
    def get_size(self) -> Tuple[int, int]:
        """Get current terminal size."""
        if self.last_size is None:
            self.last_size = get_terminal_size()
        return self.last_size