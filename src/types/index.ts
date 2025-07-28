/**
 * LocalDocs Type Definitions
 * TypeScript interfaces and types for the LocalDocs application
 */

export interface DocumentMetadata {
  url: string;
  name?: string;
  description?: string;
  tags: string[];
}

export interface LocalDocsConfig {
  storage_directory: string;
  documents: Record<string, DocumentMetadata>;
}

export interface ExportOptions {
  format: 'toc' | 'claude' | 'json';
  softLinks: boolean;
  includeDocs?: string[];
  tagFilters?: string[];
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export interface TerminalSize {
  width: number;
  height: number;
}

export interface KeyPress {
  name?: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  sequence?: string;
  raw?: string;
}

export interface DocumentListItem {
  hashId: string;
  metadata: DocumentMetadata;
}

export interface FilterState {
  tagFilters: Set<string>;
  availableTags: Set<string>;
}

export interface InteractiveState {
  docs: DocumentListItem[];
  selected: Set<string>;
  currentIndex: number;
  filterState: FilterState;
  inFilterMode: boolean;
  terminalSize: TerminalSize;
}

// Constants
export const MIN_TERMINAL_WIDTH = 60;
export const DEFAULT_TERMINAL_WIDTH = 80;
export const MIN_SPACING = 4;
export const HORIZONTAL_PADDING = 4;
export const DOWNLOAD_TIMEOUT = 30000; // 30 seconds in milliseconds
export const VALIDATION_TIMEOUT = 10000; // 10 seconds in milliseconds
export const MAX_NAME_COLUMN_WIDTH = 40;
export const MIN_COLUMN_WIDTH = 8;

// Command types for CLI
export interface AddCommandArgs {
  urls?: string[];
  fromFile?: string;
}

export interface SetCommandArgs {
  hashId: string;
  name?: string;
  description?: string;
  tags?: string;
}

export interface ListCommandArgs {
  tags?: string;
}

export interface UpdateCommandArgs {
  hashId?: string;
}

export interface RemoveCommandArgs {
  hashId: string;
}

export interface ExportCommandArgs {
  packageName: string;
  format: 'toc' | 'claude' | 'json';
  softLinks?: boolean;
  include?: string;
  tags?: string;
}

export interface ManageCommandArgs {
  // Interactive mode has no arguments
}

// Error types
export class LocalDocsError extends Error {
  constructor(message: string, public readonly code?: string) {
    super(message);
    this.name = 'LocalDocsError';
  }
}

export class ValidationError extends LocalDocsError {
  constructor(message: string) {
    super(message, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}

export class NetworkError extends LocalDocsError {
  constructor(message: string, public readonly url?: string) {
    super(message, 'NETWORK_ERROR');
    this.name = 'NetworkError';
  }
}

export class FileSystemError extends LocalDocsError {
  constructor(message: string, public readonly path?: string) {
    super(message, 'FILESYSTEM_ERROR');
    this.name = 'FileSystemError';
  }
}