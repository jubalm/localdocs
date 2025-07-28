/**
 * Validation utilities for LocalDocs
 * Port of validation functions from Python version
 */

import { ValidationError } from '../types/index.js';

/**
 * Validate package name for security
 */
export function validatePackageName(packageName: string): boolean {
  if (!packageName || packageName.length > 255) {
    return false;
  }

  // Disallow path traversal attempts
  if (packageName.includes('..') || packageName.startsWith('/') || packageName.startsWith('\\')) {
    return false;
  }

  // Only allow alphanumeric, hyphens, underscores, and dots
  if (!/^[a-zA-Z0-9._-]+$/.test(packageName)) {
    return false;
  }

  // Disallow reserved names
  const reservedNames = new Set([
    'con', 'prn', 'aux', 'nul',
    'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
    'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
  ]);

  if (reservedNames.has(packageName.toLowerCase())) {
    return false;
  }

  return true;
}

/**
 * Sanitize filename to prevent directory traversal
 */
export function sanitizeFilename(filename: string): string {
  // Remove path components and just keep the filename
  const basename = filename.split(/[/\\]/).pop() || '';

  // Replace dangerous characters
  let sanitized = basename.replace(/[<>:"/\\|?*]/g, '_');

  // Limit length
  if (sanitized.length > 255) {
    const lastDotIndex = sanitized.lastIndexOf('.');
    if (lastDotIndex > 0) {
      const name = sanitized.substring(0, lastDotIndex);
      const ext = sanitized.substring(lastDotIndex);
      sanitized = name.substring(0, 255 - ext.length) + ext;
    } else {
      sanitized = sanitized.substring(0, 255);
    }
  }

  return sanitized;
}

/**
 * Validate and clean tag input string. Returns list of valid tags.
 */
export function validateAndCleanTags(tagsInput: string): string[] {
  if (!tagsInput.trim()) {
    return [];
  }

  // Split by comma and clean each tag
  const rawTags = tagsInput.split(',').map(tag => tag.trim().toLowerCase());
  const validTags: string[] = [];

  for (const tag of rawTags) {
    if (!tag) {
      continue; // Skip empty strings
    }

    // Validate tag format: alphanumeric + hyphens, max 20 chars
    if (!/^[a-zA-Z0-9-]+$/.test(tag) || tag.length > 20) {
      console.warn(`Warning: Skipping invalid tag '${tag}' (use alphanumeric + hyphens, max 20 chars)`);
      continue;
    }

    // Avoid duplicates
    if (!validTags.includes(tag)) {
      validTags.push(tag);
    }
  }

  // Limit to 10 tags max
  if (validTags.length > 10) {
    console.warn('Warning: Only keeping first 10 tags (limit exceeded)');
    return validTags.slice(0, 10);
  }

  return validTags;
}

/**
 * Validate URL format
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if a string is a valid hash ID (8 character hex string)
 */
export function isValidHashId(hashId: string): boolean {
  return /^[a-f0-9]{8}$/.test(hashId);
}

/**
 * Validate export format
 */
export function isValidExportFormat(format: string): format is 'toc' | 'claude' | 'json' {
  return ['toc', 'claude', 'json'].includes(format);
}

/**
 * Comprehensive validation for document metadata
 */
export function validateDocumentMetadata(metadata: any): void {
  if (!metadata || typeof metadata !== 'object') {
    throw new ValidationError('Document metadata must be an object');
  }

  if (!metadata.url || typeof metadata.url !== 'string') {
    throw new ValidationError('Document metadata must have a valid URL');
  }

  if (!isValidUrl(metadata.url)) {
    throw new ValidationError(`Invalid URL format: ${metadata.url}`);
  }

  if (metadata.name !== undefined && metadata.name !== null && typeof metadata.name !== 'string') {
    throw new ValidationError('Document name must be a string');
  }

  if (metadata.description !== undefined && metadata.description !== null && typeof metadata.description !== 'string') {
    throw new ValidationError('Document description must be a string');
  }

  if (metadata.tags !== undefined && metadata.tags !== null) {
    if (!Array.isArray(metadata.tags)) {
      throw new ValidationError('Document tags must be an array');
    }

    for (const tag of metadata.tags) {
      if (typeof tag !== 'string') {
        throw new ValidationError('All tags must be strings');
      }
    }
  }
}