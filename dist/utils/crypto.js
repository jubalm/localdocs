"use strict";
/**
 * Cryptographic utilities for LocalDocs
 * Handles hash generation for document IDs
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateHashId = generateHashId;
exports.generateFilename = generateFilename;
const crypto_1 = require("crypto");
/**
 * Generate hash ID from URL for filename
 * Mimics the Python _generate_hash_id function
 */
function generateHashId(url) {
    return (0, crypto_1.createHash)('sha256').update(url, 'utf-8').digest('hex').substring(0, 8);
}
/**
 * Generate hash-based filename
 * Mimics the Python _generate_filename function
 */
function generateFilename(url) {
    const hashId = generateHashId(url);
    return `${hashId}.md`;
}
//# sourceMappingURL=crypto.js.map