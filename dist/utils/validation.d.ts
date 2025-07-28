/**
 * Validation utilities for LocalDocs
 * Port of validation functions from Python version
 */
/**
 * Validate package name for security
 */
export declare function validatePackageName(packageName: string): boolean;
/**
 * Sanitize filename to prevent directory traversal
 */
export declare function sanitizeFilename(filename: string): string;
/**
 * Validate and clean tag input string. Returns list of valid tags.
 */
export declare function validateAndCleanTags(tagsInput: string): string[];
/**
 * Validate URL format
 */
export declare function isValidUrl(url: string): boolean;
/**
 * Check if a string is a valid hash ID (8 character hex string)
 */
export declare function isValidHashId(hashId: string): boolean;
/**
 * Validate export format
 */
export declare function isValidExportFormat(format: string): format is 'toc' | 'claude' | 'json';
/**
 * Comprehensive validation for document metadata
 */
export declare function validateDocumentMetadata(metadata: any): void;
//# sourceMappingURL=validation.d.ts.map