"use strict";
/**
 * CLI Implementation using commander.js
 * TypeScript port of the Python CLI interface
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createCLI = createCLI;
exports.runCLI = runCLI;
const commander_1 = require("commander");
const chalk_1 = __importDefault(require("chalk"));
const index_js_1 = require("../managers/index.js");
const validation_js_1 = require("../utils/validation.js");
/**
 * Create and configure the CLI program
 */
function createCLI() {
    const program = new commander_1.Command();
    program
        .name('localdocs')
        .description('LocalDocs - Simple documentation downloader optimized for LLM workflows')
        .version('0.1.0');
    // Add command
    const addCmd = program
        .command('add')
        .description('Download documents')
        .argument('[urls...]', 'URLs to download')
        .option('-f, --from-file <file>', 'Read URLs from file')
        .action(async (urls, options) => {
        await handleAddCommand({ urls, fromFile: options.fromFile });
    });
    // Set command
    const setCmd = program
        .command('set')
        .description('Set document metadata')
        .argument('<hash-id>', 'Document hash ID')
        .option('-n, --name <name>', 'Document name')
        .option('-d, --description <description>', 'Document description')
        .option('-t, --tags <tags>', 'Comma-separated tags (e.g., "frontend,react,tutorial")')
        .action(async (hashId, options) => {
        await handleSetCommand({
            hashId,
            name: options.name,
            description: options.description,
            tags: options.tags,
        });
    });
    // List command
    const listCmd = program
        .command('list')
        .description('List all documents')
        .option('--tags <tags>', 'Filter by tags (comma-separated, AND logic)')
        .action(async (options) => {
        await handleListCommand({ tags: options.tags });
    });
    // Update command
    const updateCmd = program
        .command('update')
        .description('Update documents')
        .argument('[hash-id]', 'Specific document to update')
        .action(async (hashId) => {
        await handleUpdateCommand({ hashId });
    });
    // Remove command
    const removeCmd = program
        .command('remove')
        .description('Remove document')
        .argument('<hash-id>', 'Document hash ID')
        .action(async (hashId) => {
        await handleRemoveCommand({ hashId });
    });
    // Export command
    const exportCmd = program
        .command('export')
        .description('Export documentation packages')
        .argument('<package-name>', 'Package directory name')
        .option('--format <format>', 'Export format (toc, claude, json)', 'toc')
        .option('--soft-links', 'Use absolute paths without copying files')
        .option('--include <docs>', 'Comma-separated list of document IDs to include (default: all documents)')
        .option('--tags <tags>', 'Filter by tags (comma-separated, AND logic) - can combine with --include')
        .action(async (packageName, options) => {
        await handleExportCommand({
            packageName,
            format: options.format || 'toc',
            softLinks: options.softLinks,
            include: options.include,
            tags: options.tags,
        });
    });
    // Manage command
    const manageCmd = program
        .command('manage')
        .description('Interactive document manager')
        .action(async () => {
        await handleManageCommand();
    });
    return program;
}
/**
 * Handle add command
 */
async function handleAddCommand(args) {
    try {
        const manager = new index_js_1.DocManager();
        await manager.initialize();
        if (args.fromFile) {
            await manager.addFromFile(args.fromFile);
        }
        else if (args.urls && args.urls.length > 0) {
            await manager.addMultiple(args.urls);
        }
        else {
            await manager.addInteractive();
        }
    }
    catch (error) {
        console.error(chalk_1.default.red(`Error: ${error}`));
        process.exit(1);
    }
}
/**
 * Handle set command
 */
async function handleSetCommand(args) {
    try {
        const manager = new index_js_1.DocManager();
        await manager.initialize();
        const success = await manager.setMetadata(args.hashId, args.name, args.description, args.tags);
        if (!success) {
            process.exit(1);
        }
    }
    catch (error) {
        console.error(chalk_1.default.red(`Error: ${error}`));
        process.exit(1);
    }
}
/**
 * Handle list command
 */
async function handleListCommand(args) {
    try {
        const manager = new index_js_1.DocManager();
        await manager.initialize();
        let tagFilters;
        if (args.tags) {
            tagFilters = (0, validation_js_1.validateAndCleanTags)(args.tags);
        }
        const success = await manager.listDocs(tagFilters);
        if (!success) {
            process.exit(1);
        }
    }
    catch (error) {
        console.error(chalk_1.default.red(`Error: ${error}`));
        process.exit(1);
    }
}
/**
 * Handle update command
 */
async function handleUpdateCommand(args) {
    try {
        const manager = new index_js_1.DocManager();
        await manager.initialize();
        if (args.hashId) {
            const success = await manager.updateDoc(args.hashId);
            if (!success) {
                process.exit(1);
            }
        }
        else {
            await manager.updateAll();
        }
    }
    catch (error) {
        console.error(chalk_1.default.red(`Error: ${error}`));
        process.exit(1);
    }
}
/**
 * Handle remove command
 */
async function handleRemoveCommand(args) {
    try {
        const manager = new index_js_1.DocManager();
        await manager.initialize();
        const success = await manager.removeDoc(args.hashId);
        if (!success) {
            process.exit(1);
        }
    }
    catch (error) {
        console.error(chalk_1.default.red(`Error: ${error}`));
        process.exit(1);
    }
}
/**
 * Handle export command
 */
async function handleExportCommand(args) {
    try {
        const manager = new index_js_1.DocManager();
        await manager.initialize();
        // Determine which documents to export
        if (args.include || args.tags) {
            // Start with all documents
            const config = manager.getConfig();
            let selectedDocs = { ...config.documents };
            // Apply tag filtering if specified
            if (args.tags) {
                const tagFilters = (0, validation_js_1.validateAndCleanTags)(args.tags);
                const filteredDocs = {};
                for (const [hashId, metadata] of Object.entries(selectedDocs)) {
                    if (tagFilters.some(tag => metadata.tags.includes(tag))) {
                        filteredDocs[hashId] = metadata;
                    }
                }
                selectedDocs = filteredDocs;
            }
            // Apply ID filtering if specified (further narrows selection)
            if (args.include) {
                const includeDocIds = args.include.split(',').map(id => id.trim()).filter(id => id);
                // Keep only docs that are both in tag filter results AND in include list
                const finalDocs = {};
                for (const [hashId, metadata] of Object.entries(selectedDocs)) {
                    if (includeDocIds.includes(hashId)) {
                        finalDocs[hashId] = metadata;
                    }
                }
                selectedDocs = finalDocs;
            }
            // Export selected documents
            const includeDocIds = Object.keys(selectedDocs);
            if (includeDocIds.length > 0) {
                const success = await manager.exportSelectedPackage(args.packageName, includeDocIds, args.format, args.softLinks || false);
                if (!success) {
                    process.exit(1);
                }
            }
            else {
                console.log('No documents match the specified criteria');
            }
        }
        else {
            // Export all documents (existing behavior)
            const success = await manager.exportPackage(args.packageName, args.format, args.softLinks || false);
            if (!success) {
                process.exit(1);
            }
        }
    }
    catch (error) {
        console.error(chalk_1.default.red(`Error: ${error}`));
        process.exit(1);
    }
}
/**
 * Handle manage command
 */
async function handleManageCommand() {
    try {
        const manager = new index_js_1.DocManager();
        await manager.initialize();
        const interactive = new index_js_1.InteractiveManager(manager);
        await interactive.run();
    }
    catch (error) {
        console.error(chalk_1.default.red(`Error: ${error}`));
        process.exit(1);
    }
}
/**
 * Main CLI entry point
 */
async function runCLI(argv) {
    try {
        const program = createCLI();
        await program.parseAsync(argv);
    }
    catch (error) {
        if (error.name === 'CommanderError') {
            // Commander errors are already formatted
            process.exit(1);
        }
        else {
            console.error(chalk_1.default.red(`Error: ${error.message || error}`));
            process.exit(1);
        }
    }
}
//# sourceMappingURL=index.js.map