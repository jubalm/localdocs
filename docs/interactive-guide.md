# Interactive Document Manager Guide

<div align="center">
<img src="https://github.com/user-attachments/assets/6fcace71-fab0-4991-babf-f617767d617d" alt="Interactive Manager Demo" width="600" />
</div>

The LocalDocs interactive manager provides a powerful terminal interface for managing your documentation collections when CLI commands aren't enough. It's especially useful for large collections documents, when you need bulk operations, selective exports, or want a visual overview of your documentation library.

## Interactive Mode Basics

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

Supported operations: **Delete**, **Export**, **Update**, and **Metadata editing** (single document).

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
| s | Set metadata | Edit name/description/tags of current document |
| f | Tag filters | Open visual tag filtering interface |
| q | Quit | Shows confirmation if documents selected |

## Document Tagging

LocalDocs supports tagging documents for better organization. Use `s` to edit metadata for the current document, where you can add tags alongside names and descriptions. Tags help categorize your documentation (e.g., `frontend,react,tutorial`) and enable filtering both in CLI (`localdocs list --tags frontend`) and interactive mode.

### Visual Tag Filtering

For collections with many documents, press `f` to enter tag filter mode where you can visually select which tag categories to include. Start with all tags selected (showing all documents), then deselect tags to focus on specific content. This makes it much easier to create focused exports - filter by `frontend,react` tags first, then select and export only the relevant documentation.

**Filter mode controls:**
| Key | Action |
|-----|--------|
| j/k, ↑/↓ | Navigate tags |
| Space | Toggle tag on/off |
| a | Toggle all/none |
| Enter/Esc | Exit filter mode |

## Common Usage

**Selection strategies:**
- Use 'a' to select all, then deselect unwanted items with space
- Visual selection is faster than remembering hash IDs
- Create focused exports for specific use cases

**CLI integration:**
- Use CLI commands for quick single operations
- Switch to interactive mode for complex organization
- Return to CLI for automated workflows


The interactive manager transforms LocalDocs from a simple CLI tool into a comprehensive document management system while maintaining the lightweight, zero-config philosophy.
