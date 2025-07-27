# LocalDocs LLM Reference

## Installation
```bash
npx github:jubalm/localdocs [command]
```

## Core Commands

### Add Documentation
```bash
# Single URL
npx github:jubalm/localdocs add https://docs.example.com

# Multiple URLs
npx github:jubalm/localdocs add url1 url2 url3

# From file (one URL per line)
npx github:jubalm/localdocs add -f urls.txt
```

### Extract Document Data
```bash
# All documents (table format)
npx github:jubalm/localdocs extract

# JSON format for LLM consumption
npx github:jubalm/localdocs extract --format json

# Filter by tags (OR logic)
npx github:jubalm/localdocs extract --tags frontend,react

# Specific fields only
npx github:jubalm/localdocs extract --fields id,name,tags --format json

# Just document IDs for scripting
npx github:jubalm/localdocs extract --format ids --quiet

# Count matching documents
npx github:jubalm/localdocs extract --count-only --tags frontend

# Advanced filtering
npx github:jubalm/localdocs extract --has-tags --name-contains "api"
npx github:jubalm/localdocs extract --sort-by name --limit 5
```

### Set Metadata
```bash
# Set name and description
npx github:jubalm/localdocs set HASH_ID -n "Document Name" -d "Description"

# Add tags (comma-separated, alphanumeric + hyphens, max 20 chars each)
npx github:jubalm/localdocs set HASH_ID -t "frontend,react,tutorial"

# Update all metadata
npx github:jubalm/localdocs set HASH_ID -n "Name" -d "Desc" -t "tag1,tag2"
```

### Package Documentation
```bash
# All documents (TOC format)
npx github:jubalm/localdocs package my-docs

# Claude Code format (@file references)
npx github:jubalm/localdocs package my-docs --format claude

# JSON format (embedded content)
npx github:jubalm/localdocs package my-docs --format json

# Filter by tags (OR logic)
npx github:jubalm/localdocs package frontend-docs --tags frontend,react

# Specific documents only
npx github:jubalm/localdocs package selected-docs --include hash1,hash2,hash3

# Soft links (absolute paths, no file copying)
npx github:jubalm/localdocs package my-docs --soft-links
```

### Update Documents
```bash
# Single document
npx github:jubalm/localdocs update HASH_ID

# All documents
npx github:jubalm/localdocs update
```

### Remove Documents
```bash
npx github:jubalm/localdocs remove HASH_ID
```

### Interactive Manager
```bash
# Full-featured UI for bulk operations
npx github:jubalm/localdocs manage
```

## File Structure
```
project-directory/
├── localdocs.config.json    # Document registry + metadata
├── hash1234.md             # Clean markdown content
├── hash5678.md             # No frontmatter
└── hashABCD.md             # Hash-based filenames
```

## Config Format
```json
{
  "storage_directory": ".",
  "documents": {
    "a1b2c3d4": {
      "url": "https://docs.example.com",
      "name": "Example Docs",
      "description": "API documentation",
      "tags": ["api", "reference"]
    }
  }
}
```

## Package Formats

### TOC Format
Creates `index.md` with markdown links:
```markdown
# Documentation Index

- [Document Name](hash1234.md) - Description
- [Another Doc](hash5678.md) - Description
```

### Claude Format  
Creates `claude-refs.md` with @file references:
```markdown
# Documentation References

See @hash1234.md for API documentation.
See @hash5678.md for tutorial content.
```

### JSON Format
Creates `data.json` with embedded content:
```json
{
  "documents": [
    {
      "id": "hash1234",
      "name": "Document Name",
      "description": "Description", 
      "url": "https://source.url",
      "tags": ["tag1", "tag2"],
      "file": "hash1234.md",
      "content": "# Full markdown content..."
    }
  ]
}
```

## Configuration Discovery
1. Check `./localdocs.config.json` (project-specific)
2. Fallback to `~/.localdocs/localdocs.config.json` (global)

## Hash ID System
- URL → SHA256 → 8-character prefix
- Same URL always produces same hash ID
- Collision-resistant filename generation
- Example: `https://docs.python.org` → `a1b2c3d4`

## Tag System
- Format: alphanumeric + hyphens only
- Limits: 20 chars per tag, 10 tags per document  
- Filtering: OR logic (documents with ANY selected tag)
- Validation: automatic cleaning and deduplication

## Interactive Mode Keys
```
j/k/↑/↓  Navigate documents
Space    Toggle selection
a        Select/deselect all
f        Tag filter mode
d        Delete selected
x        Package selected  
u        Update selected
s        Set metadata (current doc)
q        Quit
```

## Common Patterns

### Project Documentation Setup
```bash
npx github:jubalm/localdocs add https://docs.framework.com
npx github:jubalm/localdocs set HASH_ID -n "Framework Docs" -t "framework,api"
npx github:jubalm/localdocs package project-docs --format claude
```

### Data Extraction for LLMs
```bash
# Get structured metadata for analysis
npx github:jubalm/localdocs extract --format json --fields id,name,tags

# Find specific documentation
npx github:jubalm/localdocs extract --name-contains "api" --format ids

# Count documents by category
npx github:jubalm/localdocs extract --count-only --tags frontend
```

### Bulk Tag Organization
```bash
npx github:jubalm/localdocs manage
# Use 'f' to filter, 's' to tag, 'x' to package subsets
```

### LLM Context Preparation
```bash
# Package as Claude references for immediate @file access
npx github:jubalm/localdocs package context --format claude --tags relevant,topic

# Package as JSON for API/programmatic use
npx github:jubalm/localdocs package data --format json --tags dataset

# Extract just what you need for context
npx github:jubalm/localdocs extract --format json --tags current-project --quiet
```