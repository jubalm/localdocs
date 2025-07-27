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
| s | Set metadata | Edit name/description of current document |
| f | Tag filters | Open visual tag filtering interface |
| q | Quit | Shows confirmation if documents selected |

## Tag Filtering

Press `f` to enter the **visual tag filtering mode** - a powerful way to organize and filter large document collections by tags.

### How Tag Filtering Works

**Initial State**: All tags are selected (✓), showing all documents  
**Filter by deselecting**: Uncheck tags to hide documents that only have those tags  
**Smart OR logic**: Documents with ANY selected tag remain visible

### Tag Filter Controls

| Key | Action | Notes |
|-----|--------|-------|
| j/k, ↓/↑ | Navigate tags | Move through available tags |
| Space | Toggle tag | Check/uncheck current tag |
| a | Toggle all/none | Smart toggle - all selected ↔ none selected |
| Enter/Esc | Exit filter mode | Return to document list |

### Filter Mode Workflow

1. **Start filtering**: Press `f` from main document view
2. **Review tags**: See all available tags in your collection
3. **Deselect unwanted**: Uncheck tags to filter out content
4. **See results**: Real-time count shows matching documents
5. **Return**: Press Enter/Esc to return with filters applied

### Practical Examples

**Scenario: Focus on frontend documentation**
```
> Press 'f' to enter filter mode
> Deselect 'backend', 'database', 'devops' tags
> Keep 'frontend', 'react', 'css' selected
> Press Enter to return
Result: Only frontend-related documents visible
```

**Status line shows active filters:**
- `Selected: 3/8 documents tagged frontend, react`
- `Selected: 2/5 documents tagged api, +2 more`

### Filter Benefits

- **Large collections**: Quickly focus on relevant documentation
- **Selective operations**: Bulk delete/export only filtered documents  
- **Visual clarity**: See exactly what tags are filtering your view
- **Non-destructive**: Original document selection preserved where possible

## Common Usage

**Selection strategies:**
- Use 'a' to select all, then deselect unwanted items with space
- Visual selection is faster than remembering hash IDs
- **Filter first, then select**: Use `f` to narrow down documents, then select what you need

**Tag-enhanced workflows:**
- **Filter → Select → Export**: Filter by tags, select documents, export focused collections
- **Filter → Bulk delete**: Remove outdated documentation by tag category
- **Tag organization**: Use `s` to add tags, then `f` to verify organization

**CLI integration:**
- Use CLI commands for quick single operations (`localdocs list --tags frontend`)
- Switch to interactive mode for complex organization and visual filtering
- Return to CLI for automated workflows and scripting


The interactive manager transforms LocalDocs from a simple CLI tool into a comprehensive document management system while maintaining the lightweight, zero-config philosophy.
