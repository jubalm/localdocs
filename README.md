# LocalDocs - Documentation That Works With Your Tools

Simple tool for collecting documentation locally and exporting organized collections for any workflow. **Research once, export everywhere, update whenever**.

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

### Context Engineering

<details>
<summary>Claude Code Custom Slash Commands</summary>

## Build A Claude Code Slash Command Integration

Add `/research` command by creating `./claude/commands/research.md` file with the following content:

```yaml
---
allowed-tools: Bash(npx github:jubalm/localdocs:*), Read
description: Collect and organize documentation for context engineering
---

# Goal
Research documentation based on user query in $ARGUMENTS and add create a reference sheet for claude memory using LocalDocs

Tool: LocalDocs (LD)
Command: `npx github:jubalm/localdocs`

Help Raw Output: 
[[ INSERT `npx github:jubalm/localdocs --help` OUTPUT HERE ]]

## Tasks
ALWAYS: prefer LocalDocs over WebFecth to download documentation or references

- [ ] Research and colled links from web search or known urls based on user query from $ARGUMENTS
- [ ] Feed the links to LocalDocs through `add`. DON'T add extra parameters
- [ ] Create meaningful names and descriptions to each entry in LocalDoc through `set`
- [ ] Generate a reference document through LocalDocs `export ai_docs --format claude`
```

**Usage example:**
```bash
# In Claude Code
/study https://docs.anthropic.com/claude/docs
/study @react-docs-urls.txt

# Result: Organized documentation ready for @file references
# Export: claude-refs.md with clean @file paths
```

This workflow solves the common problem of scattered documentation research by creating organized, reusable knowledge collections.
</details>

### Team Collaboration

<details>
  <summary>Team Runbook / Internal Docs</summary>

## Create A Team Runbook

Collect scattered team documentation and create organized, shareable collections:

```bash
# Collect your team's docs
npx github:jubalm/localdocs add https://api.yourcompany.com/docs
npx github:jubalm/localdocs add https://github.com/yourteam/wiki/README.md
npx github:jubalm/localdocs add https://internal-docs.com/deployment

# Organize with meaningful names
npx github:jubalm/localdocs set a1b2c3d4 -n "API Reference" -d "Company API documentation"
npx github:jubalm/localdocs set e5f6g7h8 -n "Team Wiki" -d "Development guidelines"

# Create shareable documentation package
npx github:jubalm/localdocs export team-onboarding

```

Share the ouput `team-onboarding` folder, commit in codebase or create a wiki. New team members get organized, working documentation with functioning links.
</details>

<details>
<summary>Programmable Documentation / Wiki Content</summary>

## Automated Documentation Systems

Transform collected documentation into structured data for wikis, sites, and automated workflows:

```bash
# Collect comprehensive documentation
npx github:jubalm/localdocs add https://docs.react.dev/learn
npx github:jubalm/localdocs add https://api.github.com/docs
npx github:jubalm/localdocs add https://tailwindcss.com/docs

# Organize with structured metadata
npx github:jubalm/localdocs set a1b2c3d4 -n "React Guide" -d "Component-based UI development"
npx github:jubalm/localdocs set e5f6g7h8 -n "GitHub API" -d "REST API reference and examples"
npx github:jubalm/localdocs set x9y8z7w6 -n "Tailwind CSS" -d "Utility-first CSS framework"

# Export as structured JSON
npx github:jubalm/localdocs export tech-docs --format json
```

**Integration examples:**

```javascript
// Load and process documentation data
const docsData = JSON.parse(fs.readFileSync('tech-docs/data.json'));

// Import to Notion database
await notion.databases.create({
  title: doc.name,
  content: doc.content,
  tags: [doc.description]
});

// Generate static site pages
docsData.documents.forEach(doc => {
  generatePage(`/docs/${doc.name}`, doc.content);
});

// Update wiki automatically
await wiki.updatePage(doc.name, {
  content: doc.content,
  lastUpdated: doc.updated_at
});
```

**Result**: Programmatic documentation pipeline. Collect once, deploy everywhere. Perfect for automated wiki updates, site generation, and maintaining synchronized documentation across platforms.
</details>

### Personal Knowledge Library

<details>
<summary>Curated Documentation Collection</summary>

## Build Your Portable Knowledge Base

Create a personal documentation collection that travels with you across projects:

```bash
# Build your personal knowledge base
npx github:jubalm/localdocs add https://docs.python.org/3/
npx github:jubalm/localdocs add https://go.dev/doc/
npx github:jubalm/localdocs add https://docs.rust-lang.org/book/
npx github:jubalm/localdocs add https://developer.mozilla.org/en-US/docs/Web/JavaScript

# Organize with personal metadata
npx github:jubalm/localdocs set a1b2c3d4 -n "Python Docs" -d "My go-to Python reference"
npx github:jubalm/localdocs set e5f6g7h8 -n "Go Guide" -d "Complete Go language guide"

# Export for any project
npx github:jubalm/localdocs export my-dev-refs --format claude
npx github:jubalm/localdocs export portable-docs --format toc

# Transfer to new machine/project
cp -r my-dev-refs/ /path/to/new-project/docs/
cp -r ~/.localdocs/ /path/to/backup/personal-knowledge/
```

**Result**: Portable personal knowledge base. Your curated documentation collection follows you across projects, machines, and workflows. No more re-researching the same topics.
</details>

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
| `export <name> [--format] [--soft-links]` | Create organized collections | `export my-docs --format claude` |

## How It Works

LocalDocs downloads documentation as clean markdown files with hash-based identifiers:

```
~/.localdocs/
  a1b2c3d4.md              # Clean markdown (no metadata pollution)
  e5f6g7h8.md              # Perfect for LLM consumption
  x9y8z7w6.md              # Hash-based collision-resistant names
  localdocs.config.json    # Metadata and configuration
```

**Hash-based storage**: Each URL gets a consistent 8-character identifier. Same URL always produces the same filename.

**Clean content**: Files contain only original markdown content - no frontmatter or metadata pollution.

**Flexible export**: Create organized collections with working relative links for any workflow.

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
