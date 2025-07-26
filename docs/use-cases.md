# LocalDocs Use Cases

This document provides comprehensive examples of how LocalDocs can be used across different workflows and scenarios.

## Table of Contents

- [Context Engineering](#context-engineering)
- [Team Collaboration](#team-collaboration) 
- [Personal Knowledge Library](#personal-knowledge-library)

---

## Context Engineering

### Claude Code Custom Slash Commands

Build a Claude Code slash command integration that automatically organizes documentation for context engineering.

#### Implementation

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

#### Usage Examples

```bash
# In Claude Code
/research https://docs.anthropic.com/claude/docs
/research @react-docs-urls.txt

# Result: Organized documentation ready for @file references
# Export: claude-refs.md with clean @file paths
```

#### Benefits

This workflow solves the common problem of scattered documentation research by creating organized, reusable knowledge collections. Instead of repeatedly using WebFetch for the same documentation, you build a curated collection that travels with your projects.

**Interactive Enhancement:**
When your research collection grows, use the interactive manager for visual organization:

```bash
# After collecting multiple documentation sources
npx github:jubalm/localdocs manage
# Visually select specific docs for different exports
# Export context-specific collections for different projects
```

**Key advantages:**
- **Token efficiency**: No repeated WebFetch calls for same docs
- **Organized context**: Clean @file references instead of raw content dumps
- **Reusable collections**: Documentation research becomes a permanent asset
- **Project portability**: Export collections to any new project

---

## Team Collaboration

### Team Runbook / Internal Docs

Collect scattered team documentation and create organized, shareable collections for new team member onboarding.

#### Implementation

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

#### Distribution

Share the output `team-onboarding` folder by:
- Committing to your codebase as `/docs/team-onboarding/`
- Creating a wiki page with the exported content
- Hosting as internal documentation site
- Including in new hire packages

New team members get organized, working documentation with functioning links and no broken references.

**Interactive Organization:**
For larger team documentation collections, use the interactive manager to organize and maintain your team docs:

```bash
# Visual organization of team resources
npx github:jubalm/localdocs manage
# Select relevant docs for different team roles
# Export role-specific documentation packages
```

### Programmable Documentation / Wiki Content

Transform collected documentation into structured data for wikis, sites, and automated workflows.

#### Implementation

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

#### Integration Examples

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

#### Automation Use Cases

- **Wiki synchronization**: Keep internal wikis updated with latest documentation
- **Static site generation**: Generate documentation sites from collected sources
- **CMS integration**: Import documentation into content management systems
- **Search indexing**: Feed documentation to search engines or internal search
- **API documentation**: Maintain synchronized API reference across platforms

**Result**: Programmatic documentation pipeline. Collect once, deploy everywhere. Perfect for automated wiki updates, site generation, and maintaining synchronized documentation across platforms.

---

## Personal Knowledge Library

### Curated Documentation Collection

Build your own personal documentation collection that travels with you across projects and machines.

#### Implementation

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

#### Personal Workflow Benefits

**Knowledge persistence**: Your research and curation efforts become permanent assets that follow you across:
- New projects
- Job changes
- Machine migrations
- Development environments

**Customized organization**: Tag and describe documentation based on your personal understanding and use patterns.

**Instant project setup**: New projects get instant access to your curated knowledge base without re-research.

#### Advanced Personal Use Cases

**Technology learning paths**:
```bash
# Create learning collections
npx github:jubalm/localdocs add https://reactjs.org/tutorial/
npx github:jubalm/localdocs add https://nextjs.org/learn
npx github:jubalm/localdocs set tutorial1234 -n "React Tutorial" -d "Step 1: Component basics"
npx github:jubalm/localdocs export react-learning-path
```

**Reference libraries by topic**:
```bash
# Backend development references
npx github:jubalm/localdocs add https://docs.djangoproject.com/
npx github:jubalm/localdocs add https://flask.palletsprojects.com/
npx github:jubalm/localdocs export backend-refs --format claude

# Frontend development references  
npx github:jubalm/localdocs add https://vuejs.org/guide/
npx github:jubalm/localdocs add https://svelte.dev/docs
npx github:jubalm/localdocs export frontend-refs --format claude
```

**Project-specific research**:
```bash
# For each new project, create dedicated collection
npx github:jubalm/localdocs add https://specific-framework-docs.com
npx github:jubalm/localdocs export project-xyz-docs
# Export travels with the project
```

**Interactive Management for Large Collections:**
As your personal knowledge base grows, the interactive manager becomes invaluable:

```bash
# Visual organization of your knowledge base
npx github:jubalm/localdocs manage
# Quick selection of docs for specific projects
# Bulk updates to keep everything current
# Clean exports for different contexts
```

**Result**: Portable personal knowledge base. Your curated documentation collection follows you across projects, machines, and workflows. No more re-researching the same topics or losing valuable research work.

---

## Summary

LocalDocs excels in scenarios where documentation needs to be:
- **Organized and reusable** (Context Engineering)
- **Shared and collaborative** (Team Collaboration)  
- **Portable and persistent** (Personal Knowledge Library)

The common thread is transforming scattered online documentation into organized, offline collections that can be exported and integrated into various workflows and tools.