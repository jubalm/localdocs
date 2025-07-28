/**
 * InteractiveManager - Interactive terminal interface for managing documents
 * TypeScript port of the Python InteractiveManager class
 */
import { DocManager } from './DocManager.js';
export declare class InteractiveManager {
    private manager;
    private state;
    constructor(docManager: DocManager);
    /**
     * Main interactive loop
     */
    run(): Promise<boolean>;
    /**
     * Collect all unique tags from the document collection
     */
    private collectAvailableTags;
    /**
     * Get documents filtered by current tag filters
     */
    private getFilteredDocs;
    /**
     * Update the docs list with current filtering and clean up invalid selections
     */
    private updateDocsList;
    /**
     * Render the main interface
     */
    private renderInterface;
    /**
     * Render documents in tree layout for narrow terminals
     */
    private renderTreeLayout;
    /**
     * Render documents in column layout for wide terminals
     */
    private renderColumnLayout;
    /**
     * Render control instructions at bottom of interface
     */
    private renderControls;
    /**
     * Handle keyboard input. Returns false to quit.
     */
    private handleKey;
    /**
     * Handle delete operation with confirmation
     */
    private handleDelete;
    /**
     * Handle export operation with confirmation
     */
    private handleExport;
    /**
     * Handle update operation with confirmation
     */
    private handleUpdate;
    /**
     * Handle setting metadata for current document
     */
    private handleSetMetadata;
    /**
     * Handle tag filter mode interface
     */
    private handleTagFilterMode;
    /**
     * Handle quit confirmation. Returns False to quit, True to stay.
     */
    private handleQuitConfirmation;
    /**
     * Show a message and wait for keypress
     */
    private showMessage;
}
//# sourceMappingURL=InteractiveManager.d.ts.map