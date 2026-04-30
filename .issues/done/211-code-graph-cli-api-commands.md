# Issue #211: Code Graph CLI and API Commands

## Description

Implement CLI commands and API endpoints for Code-as-Graph feature, enabling users to scan repositories, find symbols, and query code relationships.

## Problem

After implementing #208 (Code-as-Graph), we need to expose the functionality through CLI and API for users to interact with.

## Expected Behavior

Users should be able to:
- Scan a repository and store code graph
- Find symbols by name
- Query relationships between code elements
- View code dependencies visually
- Search for similar code patterns

## CLI Commands

```bash
# Scan a repository
tasker code-graph scan /path/to/repo
tasker code-graph scan /path/to/repo --language python
tasker code-graph scan /path/to/repo --incremental  # Only changed files

# Find symbols
tasker code-graph find MyClass
tasker code-graph find "function_name" --type function

# Query relationships
tasker code-graph calls src/utils/helper.py
tasker code-graph depends src/core/service.py
tasker code-graph tests src/handlers/user.py

# List files in graph
tasker code-graph files --limit 50
tasker code-graph files --language python

# Show file details
tasker code-graph file src/models/user.py

# Clear graph
tasker code-graph clear
```

## API Endpoints

```bash
# Scan repository
POST /api/v1/code-graph/scan
{
  "path": "/path/to/repo",
  "language": "python",  // optional, auto-detect if not provided
  "incremental": true,   // optional, default false
  "git_aware": true      // optional, default true
}

# List files
GET /api/v1/code-graph/files?limit=50&language=python

# Get file details
GET /api/v1/code-graph/files/{file_id}

# Find symbols
GET /api/v1/code-graph/symbols?name=MyClass&type=class

# Query relationships
GET /api/v1/code-graph/relationships/{node_id}?type=calls

# Get callers of a function
GET /api/v1/code-graph/calls/{function_id}

# Get dependencies of a file
GET /api/v1/code-graph/dependencies/{file_id}

# Get tests for a file
GET /api/v1/code-graph/tests/{file_id}

# Clear graph
DELETE /api/v1/code-graph

# Get graph statistics
GET /api/v1/code-graph/stats
```

## Status

**COMPLETED**

## Priority

**HIGH** - Required for v0.9.0 feature completion

## Component

CLI, API

## Acceptance Criteria

- [x] `tasker code-graph scan` command
- [x] `tasker code-graph find` command
- [x] `tasker code-graph calls` command
- [x] `tasker code-graph depends` command
- [x] `tasker code-graph tests` command
- [x] `tasker code-graph files` command
- [x] `tasker code-graph clear` command
- [x] POST /api/v1/code-graph/scan
- [x] GET /api/v1/code-graph/files
- [x] GET /api/v1/code-graph/symbols
- [x] GET /api/v1/code-graph/relationships
- [x] DELETE /api/v1/code-graph
- [x] GET /api/v1/code-graph/stats
- [x] Proper error handling for invalid paths
- [x] Progress output for long scans

## Related Issues

- #208 - Code-as-Graph with Tree-sitter