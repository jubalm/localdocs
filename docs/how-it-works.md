# How LocalDocs Works

LocalDocs processes URLs through a simple pipeline that creates collision-resistant storage with clean markdown output. This document explains the internal mechanics and design decisions.

## Architecture Overview

LocalDocs is built around three core concepts:
1. **Deterministic hashing** - Same URL always produces the same filename
2. **Clean content storage** - Pure markdown with zero metadata pollution
3. **Flexible export system** - Multiple output formats for different workflows

## 1. URL to Hash ID Conversion

Every URL gets converted to a consistent 8-character identifier:

```
URL: https://docs.python.org/3/tutorial/
     ↓ SHA256 hash
Hash: a1b2c3d4e5f67890abcdef1234567890...
     ↓ First 8 characters  
ID:   a1b2c3d4
```

### Why SHA256?

- **Collision resistance**: Extremely unlikely for different URLs to produce the same 8-character prefix
- **Deterministic**: Same URL always produces the same hash
- **URL-agnostic**: Works with any valid URL structure
- **Fast**: Quick generation for real-time processing

### Implementation Details

The hash generation happens in the `_generate_hash_id()` method:

```python
def _generate_hash_id(self, url: str) -> str:
    """Generate hash ID from URL for filename."""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()[:8]
```

## 2. Configuration Discovery

LocalDocs uses a two-level configuration system that allows both project-specific and global usage:

```
Command executed → Check ./localdocs.config.json → Found? → Use project config
                                ↓ Not found
                 Check ~/.localdocs/localdocs.config.json → Use global config
```

### Project-Level Config
- Located at `./localdocs.config.json` in current working directory
- Allows per-project documentation collections
- Takes precedence over global config

### Global Config
- Located at `~/.localdocs/localdocs.config.json`
- Fallback when no project config exists
- Shared across all LocalDocs usage

### Config Structure

```json
{
  "storage_directory": ".",
  "documents": {
    "a1b2c3d4": {
      "url": "https://docs.python.org/3/tutorial/",
      "name": "Python Tutorial",
      "description": "Official Python 3 tutorial"
    }
  }
}
```

## 3. Add Command Workflow

The `add` command follows a straightforward pipeline:

```
localdocs add <URL>
       ↓
   Download content (with User-Agent header)
       ↓
   Generate hash ID from URL
       ↓
   Save as {hash_id}.md (clean content, no frontmatter)
       ↓
   Update config with metadata: {"url": URL, "name": null, "description": null}
```

### Download Process

Content is downloaded using Python's `urllib` with a proper User-Agent header:

```python
request = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (LocalDocs/1.0; Documentation Downloader)'
})
```

### Content Storage

- Files are saved as pure markdown with `.md` extension
- **No frontmatter** - content remains completely clean
- **No metadata pollution** - perfect for LLM consumption
- Encoding is explicitly set to UTF-8 for international content

### Metadata Tracking

The config file tracks essential metadata separately from content:
- `url`: Original source URL
- `name`: Human-readable name (initially null)
- `description`: Brief description (initially null)

## 4. Storage Structure

Documents are organized in a simple, predictable structure:

```
~/.localdocs/ (or project directory)
├── localdocs.config.json    # Document registry + metadata
├── a1b2c3d4.md             # Clean markdown content
├── e5f6g7h8.md             # No frontmatter pollution
└── x9y8z7w6.md             # Hash-based filenames prevent conflicts
```

### Benefits of This Structure

- **Collision-resistant**: Hash-based names prevent filename conflicts
- **Fast lookup**: O(1) access to any document by hash ID
- **Clean separation**: Content and metadata stored separately
- **Portable**: Entire collection can be copied/moved easily

## 5. Export System

LocalDocs creates self-contained packages with different formats for various workflows:

```
Documents + Config → Format Selection → Package Creation
                          ↓
    ┌─────────────────────┼─────────────────────┐
    ↓                     ↓                     ↓
  TOC Format         Claude Format         JSON Format
(index.md +        (claude-refs.md +      (data.json with
 all files +        all files +            embedded content)
 config)            config)
```

### TOC Format (Default)
- Creates `index.md` with human-readable table of contents
- Includes all markdown files with relative links
- Perfect for documentation websites and wikis

### Claude Format
- Creates `claude-refs.md` with `@file` references
- Optimized for LLM context engineering
- Enables instant documentation access in Claude Code

### JSON Format
- Creates `data.json` with embedded content
- Self-contained single file
- Perfect for APIs, databases, and programmatic use

### Package Structure

Standard export package includes:
```
my-export/
├── index.md (or claude-refs.md, or data.json)
├── a1b2c3d4.md
├── e5f6g7h8.md
├── x9y8z7w6.md
└── localdocs.config.json
```

## 6. Update Mechanism

Documents can be refreshed individually or in batch:

- **Individual**: `localdocs update a1b2c3d4`
- **Batch**: `localdocs update` (all documents)

The update process:
1. Looks up original URL from config
2. Re-downloads content
3. Overwrites existing `.md` file
4. Preserves existing metadata (name, description)

## Key Design Decisions

### Why Hash-Based Filenames?
- **Deterministic**: Same URL always produces same filename
- **Collision-resistant**: Extremely unlikely conflicts
- **URL-agnostic**: Works with any URL structure
- **Future-proof**: No filename length or character restrictions

### Why Separate Metadata?
- **Clean content**: Markdown files remain pure
- **LLM-optimized**: No token waste on frontmatter
- **Flexible**: Metadata can be extended without touching content

### Why Two-Level Config?
- **Project isolation**: Different projects can have different docs
- **Global fallback**: Personal knowledge base available everywhere
- **Simple discovery**: No complex configuration needed

This architecture provides a solid foundation for documentation management that scales from personal use to team workflows.