# Interactive Document Manager Guide

The LocalDocs interactive manager provides a powerful terminal interface for managing your documentation collections when CLI commands aren't enough.

## When to Use Interactive Mode

The interactive manager shines when you need:

- **Visual overview** of your document collection
- **Bulk operations** on multiple documents
- **Selective exports** choosing specific documents
- **Complex organization** with many documents

## Getting Started

Launch the interactive manager from any directory with a LocalDocs collection:

```bash
npx github:jubalm/localdocs manage
```

If you don't have any documents yet, add some first:

```bash
npx github:jubalm/localdocs add https://docs.example.com
npx github:jubalm/localdocs manage
```

The interface automatically adapts to your terminal width - column layout for wide terminals, tree layout for narrow ones.

## Bulk Operations

The interactive manager's primary strength is **bulk operations**. Instead of managing documents one by one with CLI commands, you can:

1. **Visual Selection** - Navigate and select multiple documents using j/k and spacebar
2. **Batch Processing** - Apply operations to all selected documents at once
3. **Safe Execution** - All destructive operations show confirmation prompts with document lists

**Supported Bulk Operations:**
- **Delete** - Remove multiple documents permanently
- **Export** - Create packages with only selected documents  
- **Update** - Re-download multiple documents from their URLs
- **Metadata editing** - Set names and descriptions (single document)

This approach is especially powerful for large collections where CLI commands become cumbersome.

## Keyboard Reference

| Key | Action | Notes |
|-----|--------|-------|
| j, ↓ | Move down | Navigate document list |
| k, ↑ | Move up | Navigate document list |
| Space | Toggle selection | Select/deselect current document |
| a | Select/deselect all | Smart toggle based on current state |
| d | Delete selected | Shows confirmation with document list |
| x | Export selected | Prompts for package name and format |
| u | Update selected | Re-downloads from original URLs |
| s | Set metadata | Edit name/description of current document |
| q | Quit | Shows confirmation if documents selected |

## Best Practices

**When to use interactive mode:**
- Collections with 5+ documents
- Need to organize or review your documentation library
- Selective exports for different projects or teams
- Bulk maintenance operations

**Selection strategies:**
- Use 'a' to select all, then deselect unwanted items with space
- Visual selection is faster than remembering hash IDs
- Create focused exports for specific use cases

**CLI integration:**
- Use CLI commands for quick single operations
- Switch to interactive mode for complex organization
- Return to CLI for automated workflows

## Troubleshooting

**Terminal compatibility:** Works on Unix/Linux/macOS terminals, Windows via WSL or modern terminal apps.

**Performance:** Handles large collections (50+ documents) efficiently with real-time updates and minimal memory usage.

The interactive manager transforms LocalDocs from a simple CLI tool into a comprehensive document management system while maintaining the lightweight, zero-config philosophy.