"use strict";
/**
 * Filesystem utilities for LocalDocs
 * Handles file operations, config management, and path resolution
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.findConfigPath = findConfigPath;
exports.loadConfig = loadConfig;
exports.saveConfig = saveConfig;
exports.ensureDir = ensureDir;
exports.fileExists = fileExists;
exports.readFile = readFile;
exports.writeFile = writeFile;
exports.deleteFile = deleteFile;
exports.copyFile = copyFile;
const fs_1 = require("fs");
const path_1 = require("path");
const os_1 = require("os");
const index_js_1 = require("../types/index.js");
/**
 * Simple two-level config discovery
 * Mimics the Python find_config_path function
 */
async function findConfigPath() {
    const cwd = process.cwd();
    const cwdConfig = (0, path_1.join)(cwd, 'localdocs.config.json');
    try {
        await fs_1.promises.access(cwdConfig);
        return cwdConfig;
    }
    catch {
        // Fallback to global config
        return (0, path_1.join)((0, os_1.homedir)(), '.localdocs', 'localdocs.config.json');
    }
}
/**
 * Load configuration file or create default if it doesn't exist
 */
async function loadConfig(configPath) {
    try {
        const data = await fs_1.promises.readFile(configPath, 'utf-8');
        const config = JSON.parse(data);
        // Clean up old fields from previous versions
        const configAny = config;
        if ('max_keep_versions' in configAny) {
            delete configAny.max_keep_versions;
        }
        // Migrate documents to include tags field
        migrateTagsField(config);
        return config;
    }
    catch (error) {
        if (error.code === 'ENOENT') {
            // File doesn't exist, return default config
            return {
                storage_directory: '.',
                documents: {},
            };
        }
        throw new index_js_1.FileSystemError(`Failed to load config: ${error.message}`, configPath);
    }
}
/**
 * Save configuration to disk
 */
async function saveConfig(configPath, config) {
    try {
        // Ensure directory exists
        const dir = (0, path_1.dirname)(configPath);
        await fs_1.promises.mkdir(dir, { recursive: true });
        // Write config file
        await fs_1.promises.writeFile(configPath, JSON.stringify(config, null, 2), 'utf-8');
    }
    catch (error) {
        throw new index_js_1.FileSystemError(`Failed to save config: ${error.message}`, configPath);
    }
}
/**
 * Migrate documents to include tags field for backward compatibility
 */
function migrateTagsField(config) {
    if (config.documents) {
        for (const metadata of Object.values(config.documents)) {
            if (!Array.isArray(metadata.tags)) {
                metadata.tags = [];
            }
        }
    }
}
/**
 * Ensure a directory exists, creating it if necessary
 */
async function ensureDir(dirPath) {
    try {
        await fs_1.promises.mkdir(dirPath, { recursive: true });
    }
    catch (error) {
        throw new index_js_1.FileSystemError(`Failed to create directory: ${error.message}`, dirPath);
    }
}
/**
 * Check if a file exists
 */
async function fileExists(filePath) {
    try {
        await fs_1.promises.access(filePath);
        return true;
    }
    catch {
        return false;
    }
}
/**
 * Read file content safely
 */
async function readFile(filePath) {
    try {
        return await fs_1.promises.readFile(filePath, 'utf-8');
    }
    catch (error) {
        throw new index_js_1.FileSystemError(`Failed to read file: ${error.message}`, filePath);
    }
}
/**
 * Write file content safely
 */
async function writeFile(filePath, content) {
    try {
        await fs_1.promises.writeFile(filePath, content, 'utf-8');
    }
    catch (error) {
        throw new index_js_1.FileSystemError(`Failed to write file: ${error.message}`, filePath);
    }
}
/**
 * Delete a file safely
 */
async function deleteFile(filePath) {
    try {
        await fs_1.promises.unlink(filePath);
    }
    catch (error) {
        if (error.code !== 'ENOENT') {
            throw new index_js_1.FileSystemError(`Failed to delete file: ${error.message}`, filePath);
        }
    }
}
/**
 * Copy a file from source to destination
 */
async function copyFile(sourcePath, destPath) {
    try {
        await fs_1.promises.copyFile(sourcePath, destPath);
    }
    catch (error) {
        throw new index_js_1.FileSystemError(`Failed to copy file: ${error.message}`, sourcePath);
    }
}
//# sourceMappingURL=filesystem.js.map