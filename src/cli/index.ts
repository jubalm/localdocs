/**
 * CLI Implementation using commander.js
 * TypeScript port of the Python CLI interface
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { DocManager, InteractiveManager } from '../managers/index.js';
import { validateAndCleanTags } from '../utils/validation.js';
import {
  AddCommandArgs,
  SetCommandArgs,
  ListCommandArgs,
  UpdateCommandArgs,
  RemoveCommandArgs,
  ExportCommandArgs,
} from '../types/index.js';

/**
 * Create and configure the CLI program
 */
export function createCLI(): Command {
  const program = new Command();

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
    .action(async (urls: string[], options: { fromFile?: string }) => {
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
    .action(async (hashId: string, options: { name?: string; description?: string; tags?: string }) => {
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
    .action(async (options: { tags?: string }) => {
      await handleListCommand({ tags: options.tags });
    });

  // Update command
  const updateCmd = program
    .command('update')
    .description('Update documents')
    .argument('[hash-id]', 'Specific document to update')
    .action(async (hashId?: string) => {
      await handleUpdateCommand({ hashId });
    });

  // Remove command
  const removeCmd = program
    .command('remove')
    .description('Remove document')
    .argument('<hash-id>', 'Document hash ID')
    .action(async (hashId: string) => {
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
    .action(async (packageName: string, options: {
      format?: string;
      softLinks?: boolean;
      include?: string;
      tags?: string;
    }) => {
      await handleExportCommand({
        packageName,
        format: (options.format as 'toc' | 'claude' | 'json') || 'toc',
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
async function handleAddCommand(args: AddCommandArgs): Promise<void> {
  try {
    const manager = new DocManager();
    await manager.initialize();

    if (args.fromFile) {
      await manager.addFromFile(args.fromFile);
    } else if (args.urls && args.urls.length > 0) {
      await manager.addMultiple(args.urls);
    } else {
      await manager.addInteractive();
    }
  } catch (error) {
    console.error(chalk.red(`Error: ${error}`));
    process.exit(1);
  }
}

/**
 * Handle set command
 */
async function handleSetCommand(args: SetCommandArgs): Promise<void> {
  try {
    const manager = new DocManager();
    await manager.initialize();

    const success = await manager.setMetadata(args.hashId, args.name, args.description, args.tags);
    if (!success) {
      process.exit(1);
    }
  } catch (error) {
    console.error(chalk.red(`Error: ${error}`));
    process.exit(1);
  }
}

/**
 * Handle list command
 */
async function handleListCommand(args: ListCommandArgs): Promise<void> {
  try {
    const manager = new DocManager();
    await manager.initialize();

    let tagFilters: string[] | undefined;
    if (args.tags) {
      tagFilters = validateAndCleanTags(args.tags);
    }

    const success = await manager.listDocs(tagFilters);
    if (!success) {
      process.exit(1);
    }
  } catch (error) {
    console.error(chalk.red(`Error: ${error}`));
    process.exit(1);
  }
}

/**
 * Handle update command
 */
async function handleUpdateCommand(args: UpdateCommandArgs): Promise<void> {
  try {
    const manager = new DocManager();
    await manager.initialize();

    if (args.hashId) {
      const success = await manager.updateDoc(args.hashId);
      if (!success) {
        process.exit(1);
      }
    } else {
      await manager.updateAll();
    }
  } catch (error) {
    console.error(chalk.red(`Error: ${error}`));
    process.exit(1);
  }
}

/**
 * Handle remove command
 */
async function handleRemoveCommand(args: RemoveCommandArgs): Promise<void> {
  try {
    const manager = new DocManager();
    await manager.initialize();

    const success = await manager.removeDoc(args.hashId);
    if (!success) {
      process.exit(1);
    }
  } catch (error) {
    console.error(chalk.red(`Error: ${error}`));
    process.exit(1);
  }
}

/**
 * Handle export command
 */
async function handleExportCommand(args: ExportCommandArgs): Promise<void> {
  try {
    const manager = new DocManager();
    await manager.initialize();

    // Determine which documents to export
    if (args.include || args.tags) {
      // Start with all documents
      const config = manager.getConfig();
      let selectedDocs = { ...config.documents };

      // Apply tag filtering if specified
      if (args.tags) {
        const tagFilters = validateAndCleanTags(args.tags);
        const filteredDocs: Record<string, any> = {};
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
        const finalDocs: Record<string, any> = {};
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
        const success = await manager.exportSelectedPackage(
          args.packageName,
          includeDocIds,
          args.format,
          args.softLinks || false
        );
        if (!success) {
          process.exit(1);
        }
      } else {
        console.log('No documents match the specified criteria');
      }
    } else {
      // Export all documents (existing behavior)
      const success = await manager.exportPackage(
        args.packageName,
        args.format,
        args.softLinks || false
      );
      if (!success) {
        process.exit(1);
      }
    }
  } catch (error) {
    console.error(chalk.red(`Error: ${error}`));
    process.exit(1);
  }
}

/**
 * Handle manage command
 */
async function handleManageCommand(): Promise<void> {
  try {
    const manager = new DocManager();
    await manager.initialize();

    const interactive = new InteractiveManager(manager);
    await interactive.run();
  } catch (error) {
    console.error(chalk.red(`Error: ${error}`));
    process.exit(1);
  }
}

/**
 * Main CLI entry point
 */
export async function runCLI(argv?: string[]): Promise<void> {
  try {
    const program = createCLI();
    await program.parseAsync(argv);
  } catch (error: any) {
    if (error.name === 'CommanderError') {
      // Commander errors are already formatted
      process.exit(1);
    } else {
      console.error(chalk.red(`Error: ${error.message || error}`));
      process.exit(1);
    }
  }
}