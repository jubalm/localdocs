# LocalDocs - Documentation That Works With Your Tools

Lightweight documentation manager for collecting sources locally and exporting organized collections for any workflow. **Research once, export everywhere, update whenever** - with interactive management when you need it.

## In A Nutshell

Collect documentation from various sources

```sh
npx github:jubalm/localdocs add 
# opens an interactive shell where you can drop documentation links
# also supports indivitual link and links from file 
```

Export organized collections for different workflows

```sh
npx github:jubalm/localdocs export project/docs 
npx github:jubalm/localdocs export claude-context --format claude
npx github:jubalm/localdocs export data-backup --format json
```

Your document collection becomes a part of your workflow. Update your sources anytime, re-export to keep everything current.

> Where is the installation? There's none.

## Example Use Cases

Here are some ways you could use LocalDocs:

- **Context Engineering** - Claude Code slash commands and LLM workflow optimization
- **Team Collaboration** - Shared runbooks, onboarding docs, and automated wiki systems  
- **Personal Knowledge Library** - Portable documentation collections that travel across projects

For detailed examples, complete code samples, and implementation guides, see **[docs/use-cases.md](docs/use-cases.md)**.

## Getting Started

### 1. Add Documentation
```bash
# Single URL
npx github:jubalm/localdocs add https://docs.example.com/guide

# Multiple URLs at once
npx github:jubalm/localdocs add url1 url2 url3

# From a file containing URLs
npx github:jubalm/localdocs add -f documentation-urls.txt

# Interactive mode (prompts for URLs)
npx github:jubalm/localdocs add
```

### 2. Organize (Optional)
```bash
# View your collection
npx github:jubalm/localdocs list

# Add meaningful names and descriptions
npx github:jubalm/localdocs set a1b2c3d4 -n "React Guide" -d "React framework documentation"
npx github:jubalm/localdocs set e5f6g7h8 -n "API Docs" -d "REST API reference"
```

### 3. Export Collections
```bash
# Documentation website (default)
npx github:jubalm/localdocs export my-docs
# Creates: my-docs/index.md + all files + config

# Claude Code integration  
npx github:jubalm/localdocs export claude-context --format claude
# Creates: claude-context/claude-refs.md with @file references

# Selective export (specific documents only)
npx github:jubalm/localdocs export team-docs --include a1b2c3d4,e5f6g7h8 --format claude
# Creates: team-docs/ with only the specified documents

# Data export
npx github:jubalm/localdocs export backup --format json
# Creates: backup/data.json with embedded content

# Lightweight references (no file copying)
npx github:jubalm/localdocs export quick-refs --soft-links
# Creates: quick-refs/index.md with absolute paths
```

### 4. Update and Maintain
```bash
# Update specific document
npx github:jubalm/localdocs update a1b2c3d4

# Update all documents
npx github:jubalm/localdocs update

# Re-export to keep collections current
npx github:jubalm/localdocs export my-docs
```

## Advanced Usage

### Interactive Document Manager

When your collection grows or you need bulk operations, use the interactive manager:

```bash
npx github:jubalm/localdocs manage
```

**Key Features:**
- **Visual selection** - Navigate with j/k, select with space, toggle all with 'a'
- **Bulk operations** - Delete, export, or update multiple documents at once

**When to use interactive mode:**
- Organizing large document collections
- Selective exports (choose specific documents)
- Bulk updates or deletions
- Visual review of your documentation library

> **Getting started tip:** Try adding a few documents first, then run `manage` to experience the interactive interface with your actual collection.

## Export Formats

| Format | Output File | Contents | Use Case |
|--------|-------------|----------|----------|
| `toc` (default) | `index.md` | Human-readable table of contents + all files + config | Documentation websites, team sharing |
| `claude` | `claude-refs.md` | @file references + all files + config | Claude Code, LLM workflows |
| `json` | `data.json` | Self-contained with embedded content | APIs, databases, backups |

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `add [urls...] [-f file]` | Download documentation | `add url1 url2` or `add -f urls.txt` |
| `list` | Show collected documents | `list` |
| `set <hash> [-n name] [-d desc]` | Add metadata | `set a1b2c3d4 -n "Guide"` |
| `update [hash]` | Re-download documents | `update` or `update a1b2c3d4` |
| `remove <hash>` | Delete document | `remove a1b2c3d4` |
| `export <name> [--format] [--soft-links] [--include]` | Create organized collections | `export my-docs --format claude --include a1b2c3d4,e5f6g7h8` |
| `manage` | Interactive document manager | `manage` - for bulk operations and visual selection |

## How It Works

LocalDocs uses hash-based storage to create collision-resistant documentation collections. URLs are converted to 8-character identifiers, content is stored as clean markdown files, and metadata is tracked separately.

**Quick overview:**
- SHA256 hash → 8-char filename (deterministic, collision-resistant)
- Two-level config discovery (project → global fallback)  
- Clean content storage (no frontmatter pollution)
- Multiple export formats (TOC, Claude, JSON)

For detailed architecture, implementation details, and design decisions, see **[docs/how-it-works.md](docs/how-it-works.md)**.

## Requirements

- **Python 3.8+** - Script execution
- **Node.js/npm** - NPX execution  
- **Internet connection** - Document downloading

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.
