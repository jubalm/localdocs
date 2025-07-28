#!/usr/bin/env node

/**
 * LocalDocs - Simple documentation downloader optimized for LLM workflows
 * Main entry point for the application
 */

import { runCLI } from './cli/index.js';

// Handle unhandled promise rejections
process.on('unhandledRejection', (error) => {
  console.error('Unhandled promise rejection:', error);
  process.exit(1);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  process.exit(1);
});

// Handle SIGINT (Ctrl+C)
process.on('SIGINT', () => {
  console.log('\\nOperation cancelled by user');
  process.exit(1);
});

// Main execution
if (require.main === module) {
  runCLI(process.argv).catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

// Export for programmatic use
export * from './types/index.js';
export * from './utils/index.js';
export * from './managers/index.js';
export * from './cli/index.js';