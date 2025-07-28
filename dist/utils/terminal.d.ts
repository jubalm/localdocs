/**
 * Terminal utilities for LocalDocs
 * Handles terminal control, keyboard input, and screen management
 */
import { KeyPress, TerminalSize } from '../types/index.js';
/**
 * Check if terminal supports interactive features
 */
export declare function isInteractiveCapable(): boolean;
/**
 * Get current terminal size with fallback
 */
export declare function getTerminalSize(): TerminalSize;
/**
 * Clear the terminal screen using ANSI escape sequences
 */
export declare function clearScreen(): void;
/**
 * Position cursor at specific row and column (1-based)
 */
export declare function setCursorPosition(row: number, col: number): void;
/**
 * Hide cursor
 */
export declare function hideCursor(): void;
/**
 * Show cursor
 */
export declare function showCursor(): void;
/**
 * Enable raw mode for terminal input
 */
export declare function enableRawMode(): void;
/**
 * Disable raw mode for terminal input
 */
export declare function disableRawMode(): void;
/**
 * Read a single keypress from stdin
 * Returns a Promise that resolves with the key information
 */
export declare function readKeyPress(): Promise<KeyPress>;
/**
 * Wait for any key press
 */
export declare function waitForKeyPress(): Promise<void>;
/**
 * Build a centered line of text for terminal output
 */
export declare function buildCenteredLine(items: string[], availableWidth: number): string;
/**
 * Truncate text to fit within specified width
 */
export declare function truncateText(text: string, maxWidth: number, suffix?: string): string;
/**
 * Word wrap text to fit within specified width
 */
export declare function wrapText(text: string, maxWidth: number): string[];
//# sourceMappingURL=terminal.d.ts.map