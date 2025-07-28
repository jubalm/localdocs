"use strict";
/**
 * Terminal utilities for LocalDocs
 * Handles terminal control, keyboard input, and screen management
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.isInteractiveCapable = isInteractiveCapable;
exports.getTerminalSize = getTerminalSize;
exports.clearScreen = clearScreen;
exports.setCursorPosition = setCursorPosition;
exports.hideCursor = hideCursor;
exports.showCursor = showCursor;
exports.enableRawMode = enableRawMode;
exports.disableRawMode = disableRawMode;
exports.readKeyPress = readKeyPress;
exports.waitForKeyPress = waitForKeyPress;
exports.buildCenteredLine = buildCenteredLine;
exports.truncateText = truncateText;
exports.wrapText = wrapText;
const process_1 = require("process");
const index_js_1 = require("../types/index.js");
/**
 * Check if terminal supports interactive features
 */
function isInteractiveCapable() {
    return process_1.stdin.isTTY && process_1.stdout.isTTY;
}
/**
 * Get current terminal size with fallback
 */
function getTerminalSize() {
    const width = process_1.stdout.columns || index_js_1.DEFAULT_TERMINAL_WIDTH;
    const height = process_1.stdout.rows || 24;
    return { width, height };
}
/**
 * Clear the terminal screen using ANSI escape sequences
 */
function clearScreen() {
    process.stdout.write('\x1b[2J\x1b[H');
}
/**
 * Position cursor at specific row and column (1-based)
 */
function setCursorPosition(row, col) {
    process.stdout.write(`\x1b[${row};${col}H`);
}
/**
 * Hide cursor
 */
function hideCursor() {
    process.stdout.write('\x1b[?25l');
}
/**
 * Show cursor
 */
function showCursor() {
    process.stdout.write('\x1b[?25h');
}
/**
 * Enable raw mode for terminal input
 */
function enableRawMode() {
    if (process_1.stdin.isTTY) {
        process_1.stdin.setRawMode(true);
    }
}
/**
 * Disable raw mode for terminal input
 */
function disableRawMode() {
    if (process_1.stdin.isTTY) {
        process_1.stdin.setRawMode(false);
    }
}
/**
 * Read a single keypress from stdin
 * Returns a Promise that resolves with the key information
 */
function readKeyPress() {
    return new Promise((resolve) => {
        const originalRawMode = process_1.stdin.isRaw;
        if (!originalRawMode) {
            enableRawMode();
        }
        const onData = (buffer) => {
            process_1.stdin.off('data', onData);
            if (!originalRawMode) {
                disableRawMode();
            }
            const key = parseKeyPress(buffer);
            resolve(key);
        };
        process_1.stdin.once('data', onData);
    });
}
/**
 * Parse raw key input buffer into KeyPress object
 */
function parseKeyPress(buffer) {
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
async function waitForKeyPress() {
    await readKeyPress();
}
/**
 * Build a centered line of text for terminal output
 */
function buildCenteredLine(items, availableWidth) {
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
function truncateText(text, maxWidth, suffix = '...') {
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
function wrapText(text, maxWidth) {
    const words = text.split(/\s+/);
    const lines = [];
    let currentLine = '';
    for (const word of words) {
        if (currentLine.length === 0) {
            currentLine = word;
        }
        else if (currentLine.length + 1 + word.length <= maxWidth) {
            currentLine += ' ' + word;
        }
        else {
            lines.push(currentLine);
            currentLine = word;
        }
    }
    if (currentLine.length > 0) {
        lines.push(currentLine);
    }
    return lines;
}
//# sourceMappingURL=terminal.js.map