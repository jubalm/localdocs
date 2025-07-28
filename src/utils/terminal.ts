/**
 * Terminal utilities for LocalDocs
 * Handles terminal control, keyboard input, and screen management
 */

import { stdout, stdin } from 'process';
import { KeyPress, TerminalSize } from '../types/index.js';
import { DEFAULT_TERMINAL_WIDTH, MIN_TERMINAL_WIDTH } from '../types/index.js';

/**
 * Check if terminal supports interactive features
 */
export function isInteractiveCapable(): boolean {
  return stdin.isTTY && stdout.isTTY;
}

/**
 * Get current terminal size with fallback
 */
export function getTerminalSize(): TerminalSize {
  const width = stdout.columns || DEFAULT_TERMINAL_WIDTH;
  const height = stdout.rows || 24;

  return { width, height };
}

/**
 * Clear the terminal screen using ANSI escape sequences
 */
export function clearScreen(): void {
  process.stdout.write('\x1b[2J\x1b[H');
}

/**
 * Position cursor at specific row and column (1-based)
 */
export function setCursorPosition(row: number, col: number): void {
  process.stdout.write(`\x1b[${row};${col}H`);
}

/**
 * Hide cursor
 */
export function hideCursor(): void {
  process.stdout.write('\x1b[?25l');
}

/**
 * Show cursor
 */
export function showCursor(): void {
  process.stdout.write('\x1b[?25h');
}

/**
 * Enable raw mode for terminal input
 */
export function enableRawMode(): void {
  if (stdin.isTTY) {
    stdin.setRawMode(true);
  }
}

/**
 * Disable raw mode for terminal input
 */
export function disableRawMode(): void {
  if (stdin.isTTY) {
    stdin.setRawMode(false);
  }
}

/**
 * Read a single keypress from stdin
 * Returns a Promise that resolves with the key information
 */
export function readKeyPress(): Promise<KeyPress> {
  return new Promise((resolve) => {
    const originalRawMode = stdin.isRaw;
    
    if (!originalRawMode) {
      enableRawMode();
    }

    const onData = (buffer: Buffer): void => {
      stdin.off('data', onData);
      
      if (!originalRawMode) {
        disableRawMode();
      }

      const key = parseKeyPress(buffer);
      resolve(key);
    };

    stdin.once('data', onData);
  });
}

/**
 * Parse raw key input buffer into KeyPress object
 */
function parseKeyPress(buffer: Buffer): KeyPress {
  const raw = buffer.toString();
  const sequence = buffer.toString('hex');

  // Handle special keys
  if (buffer.length === 1) {
    const code = buffer[0];
    
    if (code === undefined) {
      return { name: 'unknown', raw, sequence };
    }
    
    // Control characters
    if (code >= 1 && code <= 26) {
      const letter = String.fromCharCode(code + 96); // Convert to letter
      return {
        name: letter,
        ctrl: true,
        raw,
        sequence,
      };
    }
    
    // Regular characters
    if (code >= 32 && code <= 126) {
      return {
        name: raw,
        raw,
        sequence,
      };
    }
    
    // Special single-byte keys
    switch (code) {
      case 9:
        return { name: 'tab', raw, sequence };
      case 13:
        return { name: 'return', raw, sequence };
      case 27:
        return { name: 'escape', raw, sequence };
      case 127:
        return { name: 'backspace', raw, sequence };
    }
  }

  // Handle escape sequences (arrow keys, etc.)
  if (buffer.length === 3 && buffer[0] === 27 && buffer[1] === 91) {
    const code = buffer[2];
    switch (code) {
      case 65:
        return { name: 'up', raw, sequence };
      case 66:
        return { name: 'down', raw, sequence };
      case 67:
        return { name: 'right', raw, sequence };
      case 68:
        return { name: 'left', raw, sequence };
    }
  }

  // Handle other escape sequences
  if (buffer.length > 1 && buffer[0] === 27) {
    return {
      name: 'escape-sequence',
      raw,
      sequence,
    };
  }

  // Default fallback
  return {
    name: 'unknown',
    raw,
    sequence,
  };
}

/**
 * Wait for any key press
 */
export async function waitForKeyPress(): Promise<void> {
  await readKeyPress();
}

/**
 * Build a centered line of text for terminal output
 */
export function buildCenteredLine(items: string[], availableWidth: number): string {
  if (items.length === 0) {
    return '';
  }

  const numCols = items.length;
  const colWidth = Math.floor(availableWidth / numCols);

  const cells = items.map(item => {
    const padding = Math.floor((colWidth - item.length) / 2);
    const rightPadding = colWidth - padding - item.length;
    return ' '.repeat(padding) + item + ' '.repeat(rightPadding);
  });

  return cells.join('');
}

/**
 * Truncate text to fit within specified width
 */
export function truncateText(text: string, maxWidth: number, suffix: string = '...'): string {
  if (text.length <= maxWidth) {
    return text;
  }

  if (maxWidth <= suffix.length) {
    return suffix.substring(0, maxWidth);
  }

  return text.substring(0, maxWidth - suffix.length) + suffix;
}

/**
 * Word wrap text to fit within specified width
 */
export function wrapText(text: string, maxWidth: number): string[] {
  const words = text.split(/\s+/);
  const lines: string[] = [];
  let currentLine = '';

  for (const word of words) {
    if (currentLine.length === 0) {
      currentLine = word;
    } else if (currentLine.length + 1 + word.length <= maxWidth) {
      currentLine += ' ' + word;
    } else {
      lines.push(currentLine);
      currentLine = word;
    }
  }

  if (currentLine.length > 0) {
    lines.push(currentLine);
  }

  return lines;
}