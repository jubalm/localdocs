/**
 * DocManager - Main document management class
 * TypeScript port of the Python DocManager class
 */

import { join, dirname } from 'path';
import { 
  LocalDocsConfig, 
  DocumentMetadata, 
  ExportOptions,
  LocalDocsError,
  FileSystemError,
  NetworkError 
} from '../types/index.js';
import {
  findConfigPath,
  loadConfig,
  saveConfig,
  ensureDir,
  fileExists,
  readFile,
  writeFile,
  deleteFile,
  copyFile,
} from '../utils/filesystem.js';
import {
  validatePackageName,
  sanitizeFilename,
  validateAndCleanTags,
  validateDocumentMetadata,
} from '../utils/validation.js';
import {
  generateHashId,
  generateFilename,
} from '../utils/crypto.js';
import {
  downloadContent,
  validateUrl,
} from '../utils/network.js';

export class DocManager {
  private configPath: string;
  private baseDir: string;
  private contentDir: string;
  private config: LocalDocsConfig;

  constructor(configPath?: string) {
    // Initialize synchronously, load config later
    this.configPath = '';
    this.baseDir = '';
    this.contentDir = '';
    this.config = { storage_directory: '.', documents: {} };
  }

  /**
   * Initialize the DocManager asynchronously
   */
  async initialize(configPath?: string): Promise<void> {
    // Use auto-discovery if no path specified
    if (configPath === undefined) {
      this.configPath = await findConfigPath();
    } else {
      this.configPath = configPath;
    }

    this.baseDir = dirname(this.configPath);

    // Ensure directories exist
    await ensureDir(this.baseDir);

    // Load or create config
    this.config = await loadConfig(this.configPath);

    // Set content directory based on config
    const storageDir = this.config.storage_directory;
    if (storageDir === '.') {
      this.contentDir = this.baseDir;
    } else {
      this.contentDir = join(this.baseDir, storageDir);
      await ensureDir(this.contentDir);
    }

    // Only create global config when actually using it
    if (!(await fileExists(this.configPath)) && this.configPath.includes(require('os').homedir())) {
      await this.saveConfig();
    }
  }

  /**
   * Save config to disk
   */
  private async saveConfig(): Promise<void> {
    await saveConfig(this.configPath, this.config);
  }

  /**
   * Filter documents by tags using OR logic
   */
  private filterDocsByTags(docs: Record<string, DocumentMetadata>, tagFilters: string[]): Record<string, DocumentMetadata> {
    if (tagFilters.length === 0) {
      return {}; // No tags selected = show nothing
    }

    // If all available tags are selected, show all documents
    const allAvailableTags = new Set<string>();
    for (const metadata of Object.values(docs)) {
      metadata.tags.forEach(tag => allAvailableTags.add(tag));
    }

    if (new Set(tagFilters).size === allAvailableTags.size && 
        tagFilters.every(tag => allAvailableTags.has(tag))) {
      return docs; // All tags selected = show all documents
    }

    const filteredDocs: Record<string, DocumentMetadata> = {};
    for (const [hashId, metadata] of Object.entries(docs)) {
      const docTags = metadata.tags;
      // Show document if it has ANY of the selected tags, or if it has no tags and no filters
      if (tagFilters.some(tag => docTags.includes(tag)) || (docTags.length === 0 && tagFilters.length === 0)) {
        filteredDocs[hashId] = metadata;
      }
    }

    return filteredDocs;
  }

  /**
   * Download and add a document
   */
  async addDoc(url: string): Promise<string | null> {
    console.log(`Downloading ${url}...`);

    try {
      // Download content
      const content = await downloadContent(url);

      // Generate hash ID and filename
      const hashId = generateHashId(url);
      const filename = generateFilename(url);
      const filePath = join(this.contentDir, filename);

      // Save clean markdown content (no frontmatter)
      await writeFile(filePath, content);

      // Update metadata in config (preserve existing metadata)
      if (!this.config.documents[hashId]) {
        this.config.documents[hashId] = {
          url,
          name: undefined,
          description: undefined,
          tags: [],
        };
      } else {
        // Preserve existing metadata, just update URL
        this.config.documents[hashId].url = url;
      }

      await this.saveConfig();

      console.log(`✓ Downloaded as ${hashId}.md`);
      return hashId;
    } catch (error) {
      if (error instanceof NetworkError) {
        console.log(`✗ Failed to download ${url}: ${error.message}`);
      } else {
        console.log(`✗ Failed to download ${url}: ${error}`);
      }
      return null;
    }
  }

  /**
   * Download multiple documents
   */
  async addMultiple(urls: string[]): Promise<void> {
    console.log(`Downloading ${urls.length} documents...`);

    let successCount = 0;
    for (const url of urls) {
      const result = await this.addDoc(url);
      if (result) {
        successCount++;
      }
    }

    console.log(`\\nCompleted: ${successCount}/${urls.length} documents downloaded`);
  }

  /**
   * Download URLs from a file
   */
  async addFromFile(filePath: string): Promise<void> {
    try {
      const content = await readFile(filePath);
      const urls = content
        .split('\\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#'));

      if (urls.length === 0) {
        console.log(`No URLs found in ${filePath}`);
        return;
      }

      await this.addMultiple(urls);
    } catch (error) {
      console.log(`Error reading ${filePath}: ${error}`);
    }
  }

  /**
   * Interactive mode for adding URLs
   */
  async addInteractive(): Promise<void> {
    console.log('Enter URLs (one per line, empty line to finish):');
    
    // For now, we'll implement a simple version that reads from stdin
    // In a full implementation, we'd use a proper readline interface
    const urls: string[] = [];
    
    // This is a simplified version - in practice, you'd want to use readline
    // or a proper terminal input library
    console.log('Note: Interactive input not fully implemented in this version.');
    console.log('Please use the file-based input instead.');
  }

  /**
   * Set name, description, and tags for a document
   */
  async setMetadata(
    hashId: string, 
    name?: string, 
    description?: string, 
    tags?: string
  ): Promise<boolean> {
    if (!this.config.documents[hashId]) {
      console.log(`Error: Document '${hashId}' not found`);
      return false;
    }

    // Update metadata
    if (name !== undefined) {
      this.config.documents[hashId].name = name;
    }
    if (description !== undefined) {
      this.config.documents[hashId].description = description;
    }
    if (tags !== undefined) {
      const validTags = validateAndCleanTags(tags);
      this.config.documents[hashId].tags = validTags;
    }

    await this.saveConfig();

    const updates: string[] = [];
    if (name !== undefined) {
      updates.push(`name: '${name}'`);
    }
    if (description !== undefined) {
      updates.push(`description: '${description}'`);
    }
    if (tags !== undefined) {
      const tagList = this.config.documents[hashId].tags;
      if (tagList.length > 0) {
        updates.push(`tags: [${tagList.join(', ')}]`);
      } else {
        updates.push('tags: []');
      }
    }

    console.log(`Updated ${hashId}: ${updates.join(', ')}`);
    return true;
  }

  /**
   * List all documents with hash IDs, optionally filtered by tags
   */
  async listDocs(tagFilters?: string[]): Promise<boolean> {
    if (Object.keys(this.config.documents).length === 0) {
      console.log('No documents found');
      console.log("Use 'localdocs add <url>' to add documents");
      return true;
    }

    let docs = this.config.documents;

    // Apply tag filtering if specified
    if (tagFilters && tagFilters.length > 0) {
      docs = this.filterDocsByTags(docs, tagFilters);
      if (Object.keys(docs).length === 0) {
        console.log(`No documents found with tags: ${tagFilters.join(', ')}`);
        return true;
      }
    }

    // Print header
    console.log(`${'ID'.padEnd(10)} ${'Name'.padEnd(20)} ${'Tags'.padEnd(20)} Description`);
    console.log('-'.repeat(80));

    // Print documents
    for (const [hashId, metadata] of Object.entries(docs)) {
      const name = metadata.name || '[unnamed]';
      const description = metadata.description || '[no description]';
      const tags = metadata.tags;

      // Format tags for display
      const tagsStr = tags.join(',');

      // Truncate long fields for display
      const displayName = name.length > 18 ? name.substring(0, 15) + '...' : name;
      const displayTags = tagsStr.length > 18 ? tagsStr.substring(0, 15) + '...' : tagsStr;
      const displayDesc = description.length > 30 ? description.substring(0, 27) + '...' : description;

      console.log(`${hashId.padEnd(10)} ${displayName.padEnd(20)} ${displayTags.padEnd(20)} ${displayDesc}`);
    }

    // Print summary
    const totalDocs = Object.keys(this.config.documents).length;
    if (tagFilters && tagFilters.length > 0) {
      console.log(`\\nShowing: ${Object.keys(docs).length} documents with tags [${tagFilters.join(', ')}] (Total: ${totalDocs})`);
    } else {
      console.log(`\\nTotal: ${Object.keys(docs).length} documents`);
    }

    return true;
  }

  /**
   * Re-download a specific document
   */
  async updateDoc(hashId: string): Promise<boolean> {
    if (!this.config.documents[hashId]) {
      console.log(`Error: Document '${hashId}' not found`);
      return false;
    }

    const url = this.config.documents[hashId].url;
    console.log(`Updating ${hashId}...`);

    // Re-download (this will overwrite the existing file)
    const result = await this.addDoc(url);

    if (result) {
      console.log(`✓ ${hashId} updated`);
      return true;
    } else {
      console.log(`✗ ${hashId} update failed`);
      return false;
    }
  }

  /**
   * Update all documents
   */
  async updateAll(): Promise<number> {
    const docs = this.config.documents;
    if (Object.keys(docs).length === 0) {
      console.log('No documents to update');
      return 0;
    }

    console.log(`Updating ${Object.keys(docs).length} documents...`);

    let updatedCount = 0;
    for (const hashId of Object.keys(docs)) {
      if (await this.updateDoc(hashId)) {
        updatedCount++;
      }
    }

    console.log(`\\nCompleted: ${updatedCount}/${Object.keys(docs).length} documents updated`);
    return updatedCount;
  }

  /**
   * Remove a document
   */
  async removeDoc(hashId: string): Promise<boolean> {
    if (!this.config.documents[hashId]) {
      console.log(`Error: Document '${hashId}' not found`);
      return false;
    }

    // Remove file
    const filename = `${hashId}.md`;
    const filePath = join(this.contentDir, filename);
    if (await fileExists(filePath)) {
      await deleteFile(filePath);
    }

    // Remove from config
    const name = this.config.documents[hashId].name || hashId;
    delete this.config.documents[hashId];
    await this.saveConfig();

    console.log(`Removed '${name}' (${hashId})`);
    return true;
  }

  /**
   * Export selected documents as a package
   */
  async exportSelectedPackage(
    packageName: string, 
    includeDocs: string[], 
    format: 'toc' | 'claude' | 'json' = 'toc', 
    softLinks: boolean = false
  ): Promise<boolean> {
    if (Object.keys(this.config.documents).length === 0) {
      console.log('No documents available for export');
      return true;
    }

    // Validate package name for security
    if (!validatePackageName(packageName)) {
      console.log(`Error: Invalid package name '${packageName}'. Use only alphanumeric characters, hyphens, underscores, and dots.`);
      return false;
    }

    // Filter documents to only include specified IDs
    const allDocs = this.config.documents;
    const docs: Record<string, DocumentMetadata> = {};
    const missingDocs: string[] = [];

    for (const docId of includeDocs) {
      if (allDocs[docId]) {
        docs[docId] = allDocs[docId];
      } else {
        missingDocs.push(docId);
      }
    }

    if (missingDocs.length > 0) {
      console.log(`Warning: Documents not found: ${missingDocs.join(', ')}`);
    }

    if (Object.keys(docs).length === 0) {
      console.log('No valid documents to export');
      return false;
    }

    // Create package directory
    const packagePath = join(process.cwd(), packageName);
    if (await fileExists(packagePath)) {
      console.log(`Error: Directory '${packageName}' already exists`);
      return false;
    }

    try {
      await ensureDir(packagePath);
    } catch (error) {
      console.log(`Error creating directory '${packageName}': ${error}`);
      return false;
    }

    // Determine main file name based on format
    let mainFile: string;
    if (format === 'toc') {
      mainFile = 'index.md';
    } else if (format === 'claude') {
      mainFile = 'claude-refs.md';
    } else if (format === 'json') {
      mainFile = 'data.json';
    } else {
      console.log(`Unknown format: ${format}`);
      return false;
    }

    // Generate main file content
    let content: string;
    if (format === 'json') {
      // JSON is always self-contained
      content = this.generateJsonFormat(docs, true);
    } else {
      // TOC and Claude formats
      if (softLinks) {
        content = this.generateFormatWithAbsolutePaths(docs, format);
      } else {
        content = this.generateFormatWithRelativePaths(docs, format);
        // Copy files when not using soft links
        await this.copyFilesToPackage(docs, packagePath);
        // Create config file with only the exported documents
        await this.createFilteredConfig(docs, packagePath);
      }
    }

    // Write main file
    const mainFilePath = join(packagePath, mainFile);
    try {
      await writeFile(mainFilePath, content);

      if (softLinks && format !== 'json') {
        console.log(`Package '${packageName}' created with ${mainFile} (soft-links mode)`);
      } else {
        console.log(`Package '${packageName}' created with ${mainFile}`);
      }
      return true;
    } catch (error) {
      console.log(`Error writing to ${mainFilePath}: ${error}`);
      return false;
    }
  }

  /**
   * Export all documents as a package
   */
  async exportPackage(
    packageName: string, 
    format: 'toc' | 'claude' | 'json' = 'toc', 
    softLinks: boolean = false
  ): Promise<boolean> {
    if (Object.keys(this.config.documents).length === 0) {
      console.log('No documents available for export');
      return true;
    }

    // Export all documents by passing all document IDs
    const allDocIds = Object.keys(this.config.documents);
    return this.exportSelectedPackage(packageName, allDocIds, format, softLinks);
  }

  /**
   * Generate format with relative paths for package export
   */
  private generateFormatWithRelativePaths(docs: Record<string, DocumentMetadata>, format: 'toc' | 'claude'): string {
    if (format === 'toc') {
      const lines = ['# Documentation Index', ''];
      for (const [hashId, metadata] of Object.entries(docs)) {
        const name = metadata.name || `Document ${hashId}`;
        const description = metadata.description || 'No description';
        const filename = `${hashId}.md`;
        const line = `- [${name}](${filename}) - ${description}`;
        lines.push(line);
      }
      return lines.join('\\n');
    } else if (format === 'claude') {
      const lines = ['# Documentation References', ''];
      for (const [hashId, metadata] of Object.entries(docs)) {
        const name = metadata.name || hashId;
        const description = metadata.description || `${name} documentation`;
        const filename = `${hashId}.md`;
        const refLine = `See @${filename} for ${description}.`;
        lines.push(refLine);
      }
      return lines.join('\\n');
    }
    return '';
  }

  /**
   * Generate format with absolute paths for soft-links mode
   */
  private generateFormatWithAbsolutePaths(docs: Record<string, DocumentMetadata>, format: 'toc' | 'claude'): string {
    if (format === 'toc') {
      const lines = ['# Documentation Index', ''];
      for (const [hashId, metadata] of Object.entries(docs)) {
        const name = metadata.name || `Document ${hashId}`;
        const description = metadata.description || 'No description';
        const filePath = join(this.contentDir, `${hashId}.md`);
        const line = `- [${name}](${filePath}) - ${description}`;
        lines.push(line);
      }
      return lines.join('\\n');
    } else if (format === 'claude') {
      const lines = ['# Documentation References', ''];
      for (const [hashId, metadata] of Object.entries(docs)) {
        const filePath = join(this.contentDir, `${hashId}.md`);
        const name = metadata.name || hashId;
        const description = metadata.description || `${name} documentation`;
        const refLine = `See @${filePath} for ${description}.`;
        lines.push(refLine);
      }
      return lines.join('\\n');
    }
    return '';
  }

  /**
   * Generate JSON format export with optional content embedding
   */
  private generateJsonFormat(docs: Record<string, DocumentMetadata>, includeContent: boolean = false): string {
    const exportData = {
      documents: [] as any[],
    };

    for (const [hashId, metadata] of Object.entries(docs)) {
      const docData: any = {
        id: hashId,
        name: metadata.name,
        description: metadata.description,
        url: metadata.url,
        tags: metadata.tags,
        file: `${hashId}.md`,
      };

      if (includeContent) {
        // In a full implementation, we'd read and embed the actual content
        docData.content = `[Content would be embedded here for ${hashId}]`;
      }

      exportData.documents.push(docData);
    }

    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Copy markdown files to package directory
   */
  private async copyFilesToPackage(docs: Record<string, DocumentMetadata>, packagePath: string): Promise<void> {
    for (const hashId of Object.keys(docs)) {
      const sourceFile = join(this.contentDir, `${hashId}.md`);
      const destFile = join(packagePath, `${hashId}.md`);

      if (await fileExists(sourceFile)) {
        try {
          await copyFile(sourceFile, destFile);
        } catch (error) {
          console.log(`Warning: Could not copy ${hashId}.md: ${error}`);
        }
      }
    }
  }

  /**
   * Create config file with only the exported documents
   */
  private async createFilteredConfig(docs: Record<string, DocumentMetadata>, packagePath: string): Promise<void> {
    const filteredConfig: LocalDocsConfig = {
      storage_directory: '.',
      documents: docs,
    };

    const destConfig = join(packagePath, 'localdocs.config.json');
    try {
      await writeFile(destConfig, JSON.stringify(filteredConfig, null, 2));
    } catch (error) {
      console.log(`Warning: Could not create config file: ${error}`);
    }
  }

  /**
   * Get current configuration
   */
  getConfig(): LocalDocsConfig {
    return { ...this.config };
  }

  /**
   * Get content directory path
   */
  getContentDir(): string {
    return this.contentDir;
  }

  /**
   * Check if URL is valid
   */
  async validateUrl(url: string): Promise<boolean> {
    return validateUrl(url);
  }
}