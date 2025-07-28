/**
 * DocManager - Main document management class
 * TypeScript port of the Python DocManager class
 */
import { LocalDocsConfig } from '../types/index.js';
export declare class DocManager {
    private configPath;
    private baseDir;
    private contentDir;
    private config;
    constructor(configPath?: string);
    /**
     * Initialize the DocManager asynchronously
     */
    initialize(configPath?: string): Promise<void>;
    /**
     * Save config to disk
     */
    private saveConfig;
    /**
     * Filter documents by tags using OR logic
     */
    private filterDocsByTags;
    /**
     * Download and add a document
     */
    addDoc(url: string): Promise<string | null>;
    /**
     * Download multiple documents
     */
    addMultiple(urls: string[]): Promise<void>;
    /**
     * Download URLs from a file
     */
    addFromFile(filePath: string): Promise<void>;
    /**
     * Interactive mode for adding URLs
     */
    addInteractive(): Promise<void>;
    /**
     * Set name, description, and tags for a document
     */
    setMetadata(hashId: string, name?: string, description?: string, tags?: string): Promise<boolean>;
    /**
     * List all documents with hash IDs, optionally filtered by tags
     */
    listDocs(tagFilters?: string[]): Promise<boolean>;
    /**
     * Re-download a specific document
     */
    updateDoc(hashId: string): Promise<boolean>;
    /**
     * Update all documents
     */
    updateAll(): Promise<number>;
    /**
     * Remove a document
     */
    removeDoc(hashId: string): Promise<boolean>;
    /**
     * Export selected documents as a package
     */
    exportSelectedPackage(packageName: string, includeDocs: string[], format?: 'toc' | 'claude' | 'json', softLinks?: boolean): Promise<boolean>;
    /**
     * Export all documents as a package
     */
    exportPackage(packageName: string, format?: 'toc' | 'claude' | 'json', softLinks?: boolean): Promise<boolean>;
    /**
     * Generate format with relative paths for package export
     */
    private generateFormatWithRelativePaths;
    /**
     * Generate format with absolute paths for soft-links mode
     */
    private generateFormatWithAbsolutePaths;
    /**
     * Generate JSON format export with optional content embedding
     */
    private generateJsonFormat;
    /**
     * Copy markdown files to package directory
     */
    private copyFilesToPackage;
    /**
     * Create config file with only the exported documents
     */
    private createFilteredConfig;
    /**
     * Get current configuration
     */
    getConfig(): LocalDocsConfig;
    /**
     * Get content directory path
     */
    getContentDir(): string;
    /**
     * Check if URL is valid
     */
    validateUrl(url: string): Promise<boolean>;
}
//# sourceMappingURL=DocManager.d.ts.map