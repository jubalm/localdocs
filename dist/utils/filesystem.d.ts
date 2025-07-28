/**
 * Filesystem utilities for LocalDocs
 * Handles file operations, config management, and path resolution
 */
import { LocalDocsConfig } from '../types/index.js';
/**
 * Simple two-level config discovery
 * Mimics the Python find_config_path function
 */
export declare function findConfigPath(): Promise<string>;
/**
 * Load configuration file or create default if it doesn't exist
 */
export declare function loadConfig(configPath: string): Promise<LocalDocsConfig>;
/**
 * Save configuration to disk
 */
export declare function saveConfig(configPath: string, config: LocalDocsConfig): Promise<void>;
/**
 * Ensure a directory exists, creating it if necessary
 */
export declare function ensureDir(dirPath: string): Promise<void>;
/**
 * Check if a file exists
 */
export declare function fileExists(filePath: string): Promise<boolean>;
/**
 * Read file content safely
 */
export declare function readFile(filePath: string): Promise<string>;
/**
 * Write file content safely
 */
export declare function writeFile(filePath: string, content: string): Promise<void>;
/**
 * Delete a file safely
 */
export declare function deleteFile(filePath: string): Promise<void>;
/**
 * Copy a file from source to destination
 */
export declare function copyFile(sourcePath: string, destPath: string): Promise<void>;
//# sourceMappingURL=filesystem.d.ts.map