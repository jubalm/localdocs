"use strict";
/**
 * InteractiveManager - Interactive terminal interface for managing documents
 * TypeScript port of the Python InteractiveManager class
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.InteractiveManager = void 0;
const index_js_1 = require("../types/index.js");
const terminal_js_1 = require("../utils/terminal.js");
const validation_js_1 = require("../utils/validation.js");
class InteractiveManager {
    constructor(docManager) {
        this.manager = docManager;
        this.state = {
            docs: [],
            selected: new Set(),
            currentIndex: 0,
            filterState: {
                tagFilters: new Set(),
                availableTags: new Set(),
            },
            inFilterMode: false,
            terminalSize: (0, terminal_js_1.getTerminalSize)(),
        };
    }
    /**
     * Main interactive loop
     */
    async run() {
        if (!(0, terminal_js_1.isInteractiveCapable)()) {
            console.log('Interactive mode requires a terminal that supports keyboard input.');
            console.log('Use regular CLI commands instead:');
            console.log('  localdocs list    - Show all documents');
            console.log('  localdocs export  - Export documents');
            console.log('  localdocs remove  - Remove a document');
            return false;
        }
        // Load documents
        const config = this.manager.getConfig();
        if (Object.keys(config.documents).length === 0) {
            console.log("No documents found. Use 'localdocs add <url>' to add documents first.");
            return true;
        }
        // Initialize tag filtering system
        this.collectAvailableTags();
        this.state.filterState.tagFilters = new Set(this.state.filterState.availableTags);
        this.state.currentIndex = 0;
        this.state.selected = new Set();
        this.updateDocsList();
        try {
            // Initial render
            this.renderInterface();
            while (true) {
                const key = await (0, terminal_js_1.readKeyPress)();
                const shouldContinue = await this.handleKey(key);
                if (!shouldContinue) {
                    break; // User chose to quit
                }
                // Re-render after key action
                this.renderInterface();
            }
        }
        catch (error) {
            (0, terminal_js_1.clearScreen)();
            console.log('Interactive mode cancelled.');
        }
        return true;
    }
    /**
     * Collect all unique tags from the document collection
     */
    collectAvailableTags() {
        this.state.filterState.availableTags = new Set();
        const config = this.manager.getConfig();
        for (const metadata of Object.values(config.documents)) {
            metadata.tags.forEach(tag => this.state.filterState.availableTags.add(tag));
        }
    }
    /**
     * Get documents filtered by current tag filters
     */
    getFilteredDocs() {
        const config = this.manager.getConfig();
        const allDocs = config.documents;
        if (this.state.filterState.tagFilters.size === 0) {
            return allDocs;
        }
        const filteredDocs = {};
        for (const [hashId, metadata] of Object.entries(allDocs)) {
            const docTags = metadata.tags;
            // Show document if it has ANY of the selected tags
            if (Array.from(this.state.filterState.tagFilters).some(tag => docTags.includes(tag))) {
                filteredDocs[hashId] = metadata;
            }
        }
        return filteredDocs;
    }
    /**
     * Update the docs list with current filtering and clean up invalid selections
     */
    updateDocsList() {
        const filteredDocs = this.getFilteredDocs();
        this.state.docs = Object.entries(filteredDocs).map(([hashId, metadata]) => ({
            hashId,
            metadata,
        }));
        // Clean up selections - remove documents that are no longer visible
        const visibleDocIds = new Set(this.state.docs.map(doc => doc.hashId));
        this.state.selected = new Set(Array.from(this.state.selected).filter(id => visibleDocIds.has(id)));
        // Adjust current index if needed
        if (this.state.docs.length > 0) {
            this.state.currentIndex = Math.min(this.state.currentIndex, this.state.docs.length - 1);
        }
        else {
            this.state.currentIndex = 0;
        }
    }
    /**
     * Render the main interface
     */
    renderInterface() {
        (0, terminal_js_1.clearScreen)();
        console.log('LocalDocs - Document Manager');
        console.log('='.repeat(50));
        console.log();
        // Get terminal width for layout decision
        this.state.terminalSize = (0, terminal_js_1.getTerminalSize)();
        const width = this.state.terminalSize.width;
        // Display documents with layout based on terminal width
        if (width < index_js_1.MIN_TERMINAL_WIDTH) {
            this.renderTreeLayout(width);
        }
        else {
            this.renderColumnLayout(width);
        }
        // Status and controls
        console.log();
        // Create status line with tag filter information
        const config = this.manager.getConfig();
        const totalDocs = Object.keys(config.documents).length;
        if (this.state.filterState.tagFilters.size > 0) {
            // Show filtered status
            const tagList = Array.from(this.state.filterState.tagFilters).sort();
            let tagsStr;
            if (tagList.length <= 3) {
                tagsStr = tagList.join(', ');
            }
            else {
                tagsStr = `${tagList.slice(0, 3).join(', ')}, +${tagList.length - 3} more`;
            }
            console.log(`Selected: ${this.state.selected.size}/${this.state.docs.length} documents tagged ${tagsStr}`);
        }
        else {
            console.log(`Selected: ${this.state.selected.size}/${this.state.docs.length} documents`);
        }
        console.log();
        this.renderControls(width);
    }
    /**
     * Render documents in tree layout for narrow terminals
     */
    renderTreeLayout(width) {
        for (let i = 0; i < this.state.docs.length; i++) {
            const doc = this.state.docs[i];
            if (!doc)
                continue;
            const { hashId, metadata } = doc;
            // Current document indicator
            const cursor = i === this.state.currentIndex ? '>' : ' ';
            // Selection checkbox
            const checkbox = this.state.selected.has(hashId) ? '[x]' : '[ ]';
            // Document info
            const name = metadata.name || '[unnamed]';
            const description = metadata.description || '[no description]';
            const tags = metadata.tags;
            // Main line: cursor + checkbox + hash_id
            console.log(`${cursor} ${checkbox} ${hashId}`);
            // Tree branches: name, tags, and description with indentation
            console.log(`     ├─ ${name}`);
            if (tags.length > 0) {
                const tagsStr = tags.join(',');
                console.log(`     ├─ tags: ${tagsStr}`);
            }
            // Handle long descriptions by wrapping
            const descWidth = width - 8; // Account for indentation "     └─ "
            if (description.length <= descWidth) {
                console.log(`     └─ ${description}`);
            }
            else {
                // Wrap long descriptions
                const wrappedLines = (0, terminal_js_1.wrapText)(description, descWidth);
                for (let j = 0; j < wrappedLines.length; j++) {
                    if (j === 0) {
                        console.log(`     └─ ${wrappedLines[j]}`);
                    }
                    else {
                        console.log(`        ${wrappedLines[j]}`); // Plain continuation
                    }
                }
            }
            // Add spacing between documents in tree mode
            if (i < this.state.docs.length - 1) {
                console.log();
            }
        }
    }
    /**
     * Render documents in column layout for wide terminals
     */
    renderColumnLayout(width) {
        // Calculate column widths based on actual content
        // Fixed parts: cursor (1) + space (1) + checkbox (3) + spaces between columns (3)
        const fixedWidth = 8;
        const idWidth = 10; // Just wide enough for hash IDs + some padding
        const remainingWidth = width - fixedWidth - idWidth;
        let nameWidth;
        let descWidth;
        if (remainingWidth > 20) { // Ensure minimum space
            // Calculate the longest name to optimize column sizing
            let maxNameLength = 0;
            for (const { metadata } of this.state.docs) {
                const name = metadata.name || '[unnamed]';
                maxNameLength = Math.max(maxNameLength, name.length);
            }
            // Size name column to fit longest name + small buffer, but with reasonable limits
            nameWidth = Math.min(maxNameLength + 2, Math.floor(remainingWidth / 2), index_js_1.MAX_NAME_COLUMN_WIDTH);
            nameWidth = Math.max(nameWidth, index_js_1.MIN_COLUMN_WIDTH + 2);
            descWidth = Math.max(index_js_1.MIN_COLUMN_WIDTH + 2, remainingWidth - nameWidth);
        }
        else {
            // Very narrow terminal - minimal widths
            nameWidth = index_js_1.MIN_COLUMN_WIDTH;
            descWidth = Math.max(index_js_1.MIN_COLUMN_WIDTH, remainingWidth - nameWidth);
        }
        // Display documents in columns
        for (let i = 0; i < this.state.docs.length; i++) {
            const doc = this.state.docs[i];
            if (!doc)
                continue;
            const { hashId, metadata } = doc;
            // Current document indicator
            const cursor = i === this.state.currentIndex ? '>' : ' ';
            // Selection checkbox
            const checkbox = this.state.selected.has(hashId) ? '[x]' : '[ ]';
            // Document info
            const name = metadata.name || '[unnamed]';
            const description = metadata.description || '[no description]';
            // Truncate to fit calculated widths
            const displayName = (0, terminal_js_1.truncateText)(name, nameWidth);
            const displayDesc = (0, terminal_js_1.truncateText)(description, descWidth);
            console.log(`${cursor} ${checkbox} ${hashId.padEnd(idWidth)} ${displayName.padEnd(nameWidth)} ${displayDesc}`);
        }
    }
    /**
     * Render control instructions at bottom of interface
     */
    renderControls(width) {
        // Try extended labels first, then shorthand if needed
        const extendedControls = [
            '[j/k] Navigate', '[Space] Toggle selection', '[a] Select/deselect all',
            '[f] Filters', '[d] Delete', '[x] Export', '[u] Update selected',
            '[s] Set metadata', '[q] Quit'
        ];
        const shorthandControls = [
            '[j/k] Nav', '[Space] Select', '[a] All', '[f] Filters',
            '[d] Delete', '[x] Export', '[u] Update', '[s] Set', '[q] Quit'
        ];
        const minSpacing = index_js_1.MIN_SPACING; // Comfortable spacing between controls
        const horizontalPadding = index_js_1.HORIZONTAL_PADDING; // 2 spaces on each side for breathing room
        // Try extended labels first
        let totalContent = extendedControls.reduce((sum, control) => sum + control.length, 0);
        let requiredWidth = totalContent + (extendedControls.length - 1) * minSpacing + horizontalPadding;
        let controls;
        if (requiredWidth <= width) {
            // Extended labels fit - use them with natural spacing
            controls = extendedControls;
        }
        else {
            // Try shorthand labels
            totalContent = shorthandControls.reduce((sum, control) => sum + control.length, 0);
            requiredWidth = totalContent + (shorthandControls.length - 1) * minSpacing + horizontalPadding;
            if (requiredWidth <= width) {
                // Shorthand labels fit - use them with natural spacing
                controls = shorthandControls;
            }
            else {
                // Neither fit naturally - use shorthand with columns
                controls = shorthandControls;
                // Fall through to column layout
            }
        }
        // Now render with the chosen labels
        if (requiredWidth <= width) {
            // Controls fit on one line - use natural even spacing with padding
            const availableSpace = width - controls.reduce((sum, c) => sum + c.length, 0) - horizontalPadding;
            const spacesBetween = Math.max(Math.floor(availableSpace / (controls.length - 1)), minSpacing);
            let line = '  '; // Left padding
            for (let i = 0; i < controls.length; i++) {
                line += controls[i];
                if (i < controls.length - 1) { // Not the last control
                    line += ' '.repeat(spacesBetween);
                }
            }
            line += '  '; // Right padding
            console.log(line);
        }
        else {
            // Use simple 2-column centered layout with shorthand labels
            const line1 = controls.slice(0, 4); // First 4 controls
            const line2 = controls.slice(4); // Last 5 controls
            console.log((0, terminal_js_1.buildCenteredLine)(line1, width));
            console.log((0, terminal_js_1.buildCenteredLine)(line2, width));
        }
    }
    /**
     * Handle keyboard input. Returns false to quit.
     */
    async handleKey(key) {
        if (key.name === 'q') { // q - show quit confirmation
            return await this.handleQuitConfirmation(); // True = stay, False = quit
        }
        else if (key.name === 'j' || key.name === 'down') { // j or down arrow - down
            if (this.state.docs.length > 0 && this.state.currentIndex < this.state.docs.length - 1) {
                this.state.currentIndex++;
            }
        }
        else if (key.name === 'k' || key.name === 'up') { // k or up arrow - up
            if (this.state.docs.length > 0 && this.state.currentIndex > 0) {
                this.state.currentIndex--;
            }
        }
        else if (key.raw === ' ') { // Space - toggle current selection
            if (this.state.docs.length > 0 && this.state.currentIndex < this.state.docs.length) {
                const currentDoc = this.state.docs[this.state.currentIndex];
                if (currentDoc) {
                    const currentHashId = currentDoc.hashId;
                    if (this.state.selected.has(currentHashId)) {
                        this.state.selected.delete(currentHashId);
                    }
                    else {
                        this.state.selected.add(currentHashId);
                    }
                }
            }
        }
        else if (key.name === 'a') { // Smart select/deselect all
            const allHashIds = new Set(this.state.docs.map(doc => doc.hashId));
            if (this.state.selected.size === allHashIds.size) {
                // All selected - deselect all
                this.state.selected.clear();
            }
            else {
                // Some or none selected - select all
                this.state.selected = new Set(allHashIds);
            }
        }
        else if (key.name === 'd') { // Delete selected
            await this.handleDelete();
        }
        else if (key.name === 'x') { // Export selected
            await this.handleExport();
        }
        else if (key.name === 'u') { // Update selected
            await this.handleUpdate();
        }
        else if (key.name === 's') { // Set metadata for current
            await this.handleSetMetadata();
        }
        else if (key.name === 'f') { // Filter by tags
            await this.handleTagFilterMode();
        }
        return true;
    }
    /**
     * Handle delete operation with confirmation
     */
    async handleDelete() {
        if (this.state.selected.size === 0) {
            await this.showMessage('No documents selected for deletion.');
            return;
        }
        (0, terminal_js_1.clearScreen)();
        console.log('Delete the following documents?');
        console.log();
        // Show what will be deleted
        const config = this.manager.getConfig();
        for (const hashId of this.state.selected) {
            const metadata = config.documents[hashId];
            const name = metadata?.name || '[unnamed]';
            console.log(`- ${hashId} (${name})`);
        }
        console.log();
        console.log('This cannot be undone.');
        console.log('Continue? [y/N]: ');
        const key = await (0, terminal_js_1.readKeyPress)();
        if (key.name === 'y') {
            // Perform deletions
            let deletedCount = 0;
            for (const hashId of Array.from(this.state.selected)) {
                if (await this.manager.removeDoc(hashId)) {
                    deletedCount++;
                }
            }
            // Refresh docs list and clear selection
            this.updateDocsList();
            this.state.selected.clear();
            if (this.state.docs.length > 0) {
                this.state.currentIndex = Math.min(this.state.currentIndex, this.state.docs.length - 1);
            }
            else {
                this.state.currentIndex = 0;
            }
            await this.showMessage(`Deleted ${deletedCount} documents.`);
        }
        else {
            await this.showMessage('Deletion cancelled.');
        }
    }
    /**
     * Handle export operation with confirmation
     */
    async handleExport() {
        if (this.state.selected.size === 0) {
            await this.showMessage('No documents selected for export.');
            return;
        }
        (0, terminal_js_1.clearScreen)();
        console.log('Export the following documents?');
        console.log();
        // Show what will be exported
        const config = this.manager.getConfig();
        for (const hashId of this.state.selected) {
            const metadata = config.documents[hashId];
            const name = metadata?.name || '[unnamed]';
            console.log(`- ${hashId} (${name})`);
        }
        console.log();
        console.log('Package name: ');
        // For now, use a simple package name (in a full implementation, we'd read from input)
        const packageName = 'exported-docs';
        if (!(0, validation_js_1.validatePackageName)(packageName)) {
            await this.showMessage('Export cancelled - invalid package name. Use only alphanumeric characters, hyphens, underscores, and dots.');
            return;
        }
        const format = 'toc'; // Default format
        const selectedDocIds = Array.from(this.state.selected);
        const success = await this.manager.exportSelectedPackage(packageName, selectedDocIds, format, false);
        if (success) {
            await this.showMessage(`Package '${packageName}' created successfully.`);
        }
        else {
            await this.showMessage('Export failed.');
        }
    }
    /**
     * Handle update operation with confirmation
     */
    async handleUpdate() {
        if (this.state.selected.size === 0) {
            await this.showMessage('No documents selected for update.');
            return;
        }
        (0, terminal_js_1.clearScreen)();
        console.log('Update the following documents from their URLs?');
        console.log();
        // Show what will be updated
        const config = this.manager.getConfig();
        for (const hashId of this.state.selected) {
            const metadata = config.documents[hashId];
            const name = metadata?.name || '[unnamed]';
            console.log(`- ${hashId} (${name})`);
        }
        console.log();
        console.log('This will re-download content from the original URLs.');
        console.log('Continue? [Y/n]: ');
        const key = await (0, terminal_js_1.readKeyPress)();
        if (key.name !== 'n') {
            let updatedCount = 0;
            for (const hashId of this.state.selected) {
                if (await this.manager.updateDoc(hashId)) {
                    updatedCount++;
                }
            }
            await this.showMessage(`Updated ${updatedCount}/${this.state.selected.size} documents.`);
        }
        else {
            await this.showMessage('Update cancelled.');
        }
    }
    /**
     * Handle setting metadata for current document
     */
    async handleSetMetadata() {
        if (this.state.docs.length === 0 || this.state.currentIndex >= this.state.docs.length) {
            return;
        }
        const currentDoc = this.state.docs[this.state.currentIndex];
        if (!currentDoc) {
            return;
        }
        const currentHashId = currentDoc.hashId;
        const config = this.manager.getConfig();
        const metadata = config.documents[currentHashId];
        if (!metadata) {
            return;
        }
        (0, terminal_js_1.clearScreen)();
        console.log(`Edit metadata for ${currentHashId}:`);
        console.log();
        // Get current values
        const currentName = metadata?.name || '';
        const currentDesc = metadata?.description || '';
        console.log(`Name (current: ${currentName || '[unnamed]'}): `);
        console.log('Description (current: [description]): ');
        // For now, we'll use placeholder values (in a full implementation, we'd read from input)
        const newName = currentName || 'Updated Name';
        const newDescription = currentDesc || 'Updated Description';
        // Update metadata
        const nameUpdate = newName !== currentName ? newName : undefined;
        const descUpdate = newDescription !== currentDesc ? newDescription : undefined;
        await this.manager.setMetadata(currentHashId, nameUpdate, descUpdate);
        // Refresh docs list and tags (tags might have changed)
        this.collectAvailableTags();
        this.updateDocsList();
        await this.showMessage(`Updated metadata for ${currentHashId}.`);
    }
    /**
     * Handle tag filter mode interface
     */
    async handleTagFilterMode() {
        if (this.state.filterState.availableTags.size === 0) {
            await this.showMessage('No tags available in the collection.');
            return;
        }
        // Convert available tags to a sorted list for consistent ordering
        const availableTagsList = Array.from(this.state.filterState.availableTags).sort();
        let currentTagIndex = 0;
        while (true) {
            (0, terminal_js_1.clearScreen)();
            // Calculate filtered doc count
            const tempFiltered = this.getFilteredDocs();
            const filteredCount = Object.keys(tempFiltered).length;
            const config = this.manager.getConfig();
            const totalCount = Object.keys(config.documents).length;
            console.log('Filter by tags:');
            console.log();
            // Display tags with checkboxes
            for (let i = 0; i < availableTagsList.length; i++) {
                const tag = availableTagsList[i];
                if (!tag)
                    continue;
                const cursor = i === currentTagIndex ? '>' : ' ';
                const checkbox = this.state.filterState.tagFilters.has(tag) ? '[x]' : '[ ]';
                console.log(`${cursor} ${checkbox} ${tag}`);
            }
            console.log();
            console.log(`${filteredCount} documents match current filters (Total: ${totalCount})`);
            console.log();
            console.log('[j/k/↕] navigate  [space] toggle  [a] toggle all  [enter/esc] back to documents');
            const key = await (0, terminal_js_1.readKeyPress)();
            if (key.name === 'j' || key.name === 'down') {
                if (currentTagIndex < availableTagsList.length - 1) {
                    currentTagIndex++;
                }
            }
            else if (key.name === 'k' || key.name === 'up') {
                if (currentTagIndex > 0) {
                    currentTagIndex--;
                }
            }
            else if (key.name === 'escape' || key.name === 'return') {
                break; // Return to main interface
            }
            else if (key.raw === ' ' && availableTagsList.length > 0) {
                // Toggle current tag
                const currentTag = availableTagsList[currentTagIndex];
                if (currentTag) {
                    if (this.state.filterState.tagFilters.has(currentTag)) {
                        this.state.filterState.tagFilters.delete(currentTag);
                    }
                    else {
                        this.state.filterState.tagFilters.add(currentTag);
                    }
                }
                // Update docs list and clean selections
                this.updateDocsList();
            }
            else if (key.name === 'a') {
                // Smart toggle all - same logic as main interface
                if (this.state.filterState.tagFilters.size === this.state.filterState.availableTags.size) {
                    // All selected - deselect all
                    this.state.filterState.tagFilters.clear();
                }
                else {
                    // Some or none selected - select all
                    this.state.filterState.tagFilters = new Set(this.state.filterState.availableTags);
                }
                this.updateDocsList();
            }
        }
    }
    /**
     * Handle quit confirmation. Returns False to quit, True to stay.
     */
    async handleQuitConfirmation() {
        (0, terminal_js_1.clearScreen)();
        // Show context-aware message
        if (this.state.selected.size > 0) {
            const s = this.state.selected.size !== 1 ? 's' : '';
            console.log(`You have ${this.state.selected.size} document${s} selected.`);
        }
        console.log('Exit interactive manager?');
        console.log();
        console.log('[y] Yes, exit    [n] No, stay');
        while (true) {
            const key = await (0, terminal_js_1.readKeyPress)();
            if (key.name === 'y') {
                return false; // Quit the manager
            }
            else if (key.name === 'n') {
                return true; // Stay in manager
            }
            // Ignore all other keys and stay in confirmation
        }
    }
    /**
     * Show a message and wait for keypress
     */
    async showMessage(message) {
        (0, terminal_js_1.clearScreen)();
        console.log(message);
        console.log();
        console.log('Press any key to continue...');
        await (0, terminal_js_1.readKeyPress)();
    }
}
exports.InteractiveManager = InteractiveManager;
//# sourceMappingURL=InteractiveManager.js.map