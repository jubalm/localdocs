/**
 * Filesystem utilities for LocalDocs
 * Handles file operations, config management, and path resolution
 */

import { promises as fs } from 'fs';
import { dirname, join } from 'path';
import { homedir } from 'os';
import { LocalDocsConfig, FileSystemError } from '../types/index.js';

/**
 * Simple two-level config discovery
 * Mimics the Python find_config_path function
 */
export async function findConfigPath(): Promise<string> {
  const cwd = process.cwd();
  const cwdConfig = join(cwd, 'localdocs.config.json');

  try {
    await fs.access(cwdConfig);
    return cwdConfig;
  } catch {
    // Fallback to global config
    return join(homedir(), '.localdocs', 'localdocs.config.json');
  }
}

/**
 * Load configuration file or create default if it doesn't exist
 */
export async function loadConfig(configPath: string): Promise<LocalDocsConfig> {
  try {
    const data = await fs.readFile(configPath, 'utf-8');
    const config = JSON.parse(data) as LocalDocsConfig;

    // Clean up old fields from previous versions
    const configAny = config as any;
    if ('max_keep_versions' in configAny) {
      delete configAny.max_keep_versions;
    }

    // Migrate documents to include tags field
    migrateTagsField(config);

    return config;
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      // File doesn't exist, return default config
      return {
        storage_directory: '.',
        documents: {},
      };
    }
    throw new FileSystemError(`Failed to load config: ${error.message}`, configPath);
  }
}

/**
 * Save configuration to disk
 */
export async function saveConfig(configPath: string, config: LocalDocsConfig): Promise<void> {
  try {
    // Ensure directory exists
    const dir = dirname(configPath);
    await fs.mkdir(dir, { recursive: true });

    // Write config file
    await fs.writeFile(configPath, JSON.stringify(config, null, 2), 'utf-8');
  } catch (error: any) {
    throw new FileSystemError(`Failed to save config: ${error.message}`, configPath);
  }
}

/**
 * Migrate documents to include tags field for backward compatibility
 */
function migrateTagsField(config: LocalDocsConfig): void {
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
export async function ensureDir(dirPath: string): Promise<void> {
  try {
    await fs.mkdir(dirPath, { recursive: true });
  } catch (error: any) {
    throw new FileSystemError(`Failed to create directory: ${error.message}`, dirPath);
  }
}

/**
 * Check if a file exists
 */
export async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

/**
 * Read file content safely
 */
export async function readFile(filePath: string): Promise<string> {
  try {
    return await fs.readFile(filePath, 'utf-8');
  } catch (error: any) {
    throw new FileSystemError(`Failed to read file: ${error.message}`, filePath);
  }
}

/**
 * Write file content safely
 */
export async function writeFile(filePath: string, content: string): Promise<void> {
  try {
    await fs.writeFile(filePath, content, 'utf-8');
  } catch (error: any) {
    throw new FileSystemError(`Failed to write file: ${error.message}`, filePath);
  }
}

/**
 * Delete a file safely
 */
export async function deleteFile(filePath: string): Promise<void> {
  try {
    await fs.unlink(filePath);
  } catch (error: any) {
    if (error.code !== 'ENOENT') {
      throw new FileSystemError(`Failed to delete file: ${error.message}`, filePath);
    }
  }
}

/**
 * Copy a file from source to destination
 */
export async function copyFile(sourcePath: string, destPath: string): Promise<void> {
  try {
    await fs.copyFile(sourcePath, destPath);
  } catch (error: any) {
    throw new FileSystemError(`Failed to copy file: ${error.message}`, sourcePath);
  }
}