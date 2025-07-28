/**
 * Network utilities for LocalDocs
 * Handles HTTP requests and URL validation
 */
/**
 * Download content from URL
 * Mimics the Python _download_content function
 */
export declare function downloadContent(url: string): Promise<string>;
/**
 * Basic URL validation with timeout
 * Mimics the Python validate_url function
 */
export declare function validateUrl(url: string): Promise<boolean>;
/**
 * Check if URL is accessible (alternative validation method)
 */
export declare function isUrlAccessible(url: string): Promise<boolean>;
//# sourceMappingURL=network.d.ts.map