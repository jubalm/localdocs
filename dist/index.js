#!/usr/bin/env node
"use strict";
/**
 * LocalDocs - Simple documentation downloader optimized for LLM workflows
 * Main entry point for the application
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
const index_js_1 = require("./cli/index.js");
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
    (0, index_js_1.runCLI)(process.argv).catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}
// Export for programmatic use
__exportStar(require("./types/index.js"), exports);
__exportStar(require("./utils/index.js"), exports);
__exportStar(require("./managers/index.js"), exports);
__exportStar(require("./cli/index.js"), exports);
//# sourceMappingURL=index.js.map