"use strict";
/**
 * LocalDocs Type Definitions
 * TypeScript interfaces and types for the LocalDocs application
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.FileSystemError = exports.NetworkError = exports.ValidationError = exports.LocalDocsError = exports.MIN_COLUMN_WIDTH = exports.MAX_NAME_COLUMN_WIDTH = exports.VALIDATION_TIMEOUT = exports.DOWNLOAD_TIMEOUT = exports.HORIZONTAL_PADDING = exports.MIN_SPACING = exports.DEFAULT_TERMINAL_WIDTH = exports.MIN_TERMINAL_WIDTH = void 0;
// Constants
exports.MIN_TERMINAL_WIDTH = 60;
exports.DEFAULT_TERMINAL_WIDTH = 80;
exports.MIN_SPACING = 4;
exports.HORIZONTAL_PADDING = 4;
exports.DOWNLOAD_TIMEOUT = 30000; // 30 seconds in milliseconds
exports.VALIDATION_TIMEOUT = 10000; // 10 seconds in milliseconds
exports.MAX_NAME_COLUMN_WIDTH = 40;
exports.MIN_COLUMN_WIDTH = 8;
// Error types
class LocalDocsError extends Error {
    constructor(message, code) {
        super(message);
        this.code = code;
        this.name = 'LocalDocsError';
    }
}
exports.LocalDocsError = LocalDocsError;
class ValidationError extends LocalDocsError {
    constructor(message) {
        super(message, 'VALIDATION_ERROR');
        this.name = 'ValidationError';
    }
}
exports.ValidationError = ValidationError;
class NetworkError extends LocalDocsError {
    constructor(message, url) {
        super(message, 'NETWORK_ERROR');
        this.url = url;
        this.name = 'NetworkError';
    }
}
exports.NetworkError = NetworkError;
class FileSystemError extends LocalDocsError {
    constructor(message, path) {
        super(message, 'FILESYSTEM_ERROR');
        this.path = path;
        this.name = 'FileSystemError';
    }
}
exports.FileSystemError = FileSystemError;
//# sourceMappingURL=index.js.map