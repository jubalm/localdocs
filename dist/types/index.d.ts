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
export declare const MIN_TERMINAL_WIDTH = 60;
export declare const DEFAULT_TERMINAL_WIDTH = 80;
export declare const MIN_SPACING = 4;
export declare const HORIZONTAL_PADDING = 4;
export declare const DOWNLOAD_TIMEOUT = 30000;
export declare const VALIDATION_TIMEOUT = 10000;
export declare const MAX_NAME_COLUMN_WIDTH = 40;
export declare const MIN_COLUMN_WIDTH = 8;
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
}
export declare class LocalDocsError extends Error {
    readonly code?: string | undefined;
    constructor(message: string, code?: string | undefined);
}
export declare class ValidationError extends LocalDocsError {
    constructor(message: string);
}
export declare class NetworkError extends LocalDocsError {
    readonly url?: string | undefined;
    constructor(message: string, url?: string | undefined);
}
export declare class FileSystemError extends LocalDocsError {
    readonly path?: string | undefined;
    constructor(message: string, path?: string | undefined);
}
//# sourceMappingURL=index.d.ts.map