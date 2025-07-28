/**
 * Cryptographic utilities for LocalDocs
 * Handles hash generation for document IDs
 */

import { createHash } from 'crypto';

/**
 * Generate hash ID from URL for filename
 * Mimics the Python _generate_hash_id function
 */
export function generateHashId(url: string): string {
  return createHash('sha256').update(url, 'utf-8').digest('hex').substring(0, 8);
}

/**
 * Generate hash-based filename
 * Mimics the Python _generate_filename function
 */
export function generateFilename(url: string): string {
  const hashId = generateHashId(url);
  return `${hashId}.md`;
}