/**
 * Network utilities for LocalDocs
 * Handles HTTP requests and URL validation
 */

import { NetworkError } from '../types/index.js';
import { DOWNLOAD_TIMEOUT, VALIDATION_TIMEOUT } from '../types/index.js';

/**
 * Download content from URL
 * Mimics the Python _download_content function
 */
export async function downloadContent(url: string): Promise<string> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), DOWNLOAD_TIMEOUT);

    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (LocalDocs/1.0; Documentation Downloader)',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new NetworkError(`HTTP ${response.status}: ${response.statusText}`, url);
    }

    const content = await response.text();
    return content;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new NetworkError(`Download timeout after ${DOWNLOAD_TIMEOUT}ms`, url);
    }

    if (error instanceof NetworkError) {
      throw error;
    }

    throw new NetworkError(`Failed to download content: ${error.message}`, url);
  }
}

/**
 * Basic URL validation with timeout
 * Mimics the Python validate_url function
 */
export async function validateUrl(url: string): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), VALIDATION_TIMEOUT);

    const response = await fetch(url, {
      method: 'HEAD', // Use HEAD request for validation to avoid downloading content
      headers: {
        'User-Agent': 'Mozilla/5.0 (LocalDocs/1.0; Documentation Downloader)',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Check if URL is accessible (alternative validation method)
 */
export async function isUrlAccessible(url: string): Promise<boolean> {
  try {
    // First try a simple URL parse
    new URL(url);

    // Then try to access it
    return await validateUrl(url);
  } catch {
    return false;
  }
}