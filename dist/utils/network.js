"use strict";
/**
 * Network utilities for LocalDocs
 * Handles HTTP requests and URL validation
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.downloadContent = downloadContent;
exports.validateUrl = validateUrl;
exports.isUrlAccessible = isUrlAccessible;
const index_js_1 = require("../types/index.js");
const index_js_2 = require("../types/index.js");
/**
 * Download content from URL
 * Mimics the Python _download_content function
 */
async function downloadContent(url) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), index_js_2.DOWNLOAD_TIMEOUT);
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (LocalDocs/1.0; Documentation Downloader)',
            },
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new index_js_1.NetworkError(`HTTP ${response.status}: ${response.statusText}`, url);
        }
        const content = await response.text();
        return content;
    }
    catch (error) {
        if (error.name === 'AbortError') {
            throw new index_js_1.NetworkError(`Download timeout after ${index_js_2.DOWNLOAD_TIMEOUT}ms`, url);
        }
        if (error instanceof index_js_1.NetworkError) {
            throw error;
        }
        throw new index_js_1.NetworkError(`Failed to download content: ${error.message}`, url);
    }
}
/**
 * Basic URL validation with timeout
 * Mimics the Python validate_url function
 */
async function validateUrl(url) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), index_js_2.VALIDATION_TIMEOUT);
        const response = await fetch(url, {
            method: 'HEAD', // Use HEAD request for validation to avoid downloading content
            headers: {
                'User-Agent': 'Mozilla/5.0 (LocalDocs/1.0; Documentation Downloader)',
            },
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        return response.ok;
    }
    catch {
        return false;
    }
}
/**
 * Check if URL is accessible (alternative validation method)
 */
async function isUrlAccessible(url) {
    try {
        // First try a simple URL parse
        new URL(url);
        // Then try to access it
        return await validateUrl(url);
    }
    catch {
        return false;
    }
}
//# sourceMappingURL=network.js.map