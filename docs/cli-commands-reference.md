# CLI Commands Reference

Complete reference for all Tasker CLI commands with examples and options.

---

## Command Structure

All Tasker commands follow this pattern:

```
tasker <command> <subcommand> [arguments] [options]
```

### Common Options

| Option | Description |
|--------|-------------|
| `--help, -h` | Show help for command |
| `--verbose, -v` | Enable verbose output |
| `--output, -o` | Output format (json, table, text) |
| `--dry-run` | Preview changes without executing |

---

## Component Management

### `tasker component create`

Create a new component in the system.

**Syntax:**
```bash
tasker component create <name> [OPTIONS]
```

**Required:**
- `<name>` — Component name

**Options:**
- `-p, --project <project>` — Project name (default: "default")
- `-d, --description <text>` — Component description
- `--owner <email>` — Component owner
- `--tags <tag1,tag2>` — Comma-separated tags

**Examples:**

```bash
# Simple component
tasker component create auth-service

# With project
tasker component create auth-service -p backend

# Full details
tasker component create auth-service \
  -p backend \
  -d "Handles user authentication" \
  --owner dev@example.com \
  --tags auth,security,api

# Dry run (preview)
tasker component create auth-service -p backend --dry-run
```

**Output:**
```
✓ Component created: auth-service (550e8400-e29b-41d4-a716-446655440000)
```

---

### `tasker component list`

List all components, with optional filtering.

**Syntax:**
```bash
tasker component list [OPTIONS]
```

**Options:**
- `-p, --project <project>` — Filter by project
- `--owner <email>` — Filter by owner
- `--tags <tag>` — Filter by tag
- `--output, -o json|table|text` — Output format (default: table)
- `--limit <n>` — Limit results
- `--page <n>` — Pagination

**Examples:**

```bash
# List all components
tasker component list

# Filter by project
tasker component list -p backend

# Filter by owner
tasker component list --owner dev@example.com

# Filter by tag
tasker component list --tags security

# JSON output
tasker component list --output json

# Limit results
tasker component list --limit 10

# Paginate
tasker component list --page 2 --limit 20
```

**Output:**
```
ID                                   NAME              PROJECT   OWNER
550e8400-e29b-41d4-a716-446655440000 auth-service     backend   dev@example.com
550e8400-e29b-41d4-a716-446655440001 api-gateway      backend   dev@example.com
550e8400-e29b-41d4-a716-446655440002 web-ui           frontend  ui@example.com
```

---

### `tasker component show`

Display details of a specific component.

**Syntax:**
```bash
tasker component show <id|name> [OPTIONS]
```

**Arguments:**
- `<id|name>` — Component ID (UUID) or name

**Options:**
- `--include-dependencies` — Show dependencies
- `--include-issues` — Show related issues
- `--output json|table` — Output format

**Examples:**

```bash
# By ID
tasker component show 550e8400-e29b-41d4-a716-446655440000

# By name
tasker component show auth-service

# With dependencies
tasker component show auth-service --include-dependencies

# JSON output
tasker component show auth-service --output json
```

---

### `tasker component update`

Update component details.

**Syntax:**
```bash
tasker component update <id|name> [OPTIONS]
```

**Options:**
- `-d, --description <text>` — New description
- `--owner <email>` — New owner
- `--tags <tag1,tag2>` — Update tags
- `--name <new_name>` — Rename component

**Examples:**

```bash
# Update description
tasker component update auth-service -d "Handles user authentication and authorization"

# Change owner
tasker component update auth-service --owner newowner@example.com

# Update tags
tasker component update auth-service --tags auth,security,api,v2

# Rename
tasker component update auth-service --name authentication-service
```

---

### `tasker component delete`

Delete a component (and optionally related data).

**Syntax:**
```bash
tasker component delete <id|name> [OPTIONS]
```

**Options:**
- `--cascade` — Also delete related issues and dependencies
- `--force` — Skip confirmation prompt

**Examples:**

```bash
# Delete with confirmation
tasker component delete auth-service

# Delete without confirmation
tasker component delete auth-service --force

# Delete with cascading
tasker component delete auth-service --cascade
```

---

## Issue Management

### `tasker issue create`

Create a new issue.

**Syntax:**
```bash
tasker issue create <title> [OPTIONS]
```

**Required:**
- `<title>` — Issue title

**Options:**
- `-c, --component <id|name>` — Component ID or name (required)
- `-p, --priority <CRITICAL|HIGH|MEDIUM|LOW>` — Priority (default: MEDIUM)
- `-d, --description <text>` — Issue description
- `--status <OPEN|IN_PROGRESS|BLOCKED|RESOLVED|CLOSED>` — Initial status
- `--assignee <email>` — Assign to user
- `--tags <tag1,tag2>` — Tags

**Examples:**

```bash
# Simple issue
tasker issue create "Fix login bug" -c auth-service

# Full details
tasker issue create "Implement JWT refresh tokens" \
  -c auth-service \
  -p HIGH \
  -d "Add support for refresh token rotation" \
  --assignee dev@example.com \
  --tags enhancement,authentication

# In Progress immediately
tasker issue create "WIP: Database migration" \
  -c backend \
  -p CRITICAL \
  --status IN_PROGRESS
```

---

### `tasker issue list`

List issues with filtering.

**Syntax:**
```bash
tasker issue list [OPTIONS]
```

**Options:**
- `-c, --component <id|name>` — Filter by component
- `-s, --status <status>` — Filter by status (OPEN, IN_PROGRESS, etc.)
- `-p, --priority <priority>` — Filter by priority
- `--assignee <email>` — Filter by assignee
- `--tags <tag>` — Filter by tag
- `--blocked-only` — Show only blocked issues
- `--unassigned` — Show unassigned issues
- `--output json|table` — Output format
- `--limit <n>` — Limit results
- `--sort <field>` — Sort by field (priority, created, updated)

**Examples:**

```bash
# All issues
tasker issue list

# Filter by component
tasker issue list -c auth-service

# Open issues only
tasker issue list -s OPEN

# High priority issues
tasker issue list -p HIGH

# Issues assigned to you
tasker issue list --assignee dev@example.com

# Unassigned issues
tasker issue list --unassigned

# Blocked issues
tasker issue list --blocked-only

# JSON output
tasker issue list -c backend --output json

# Sort by priority
tasker issue list --sort priority
```

---

### `tasker issue show`

Display issue details.

**Syntax:**
```bash
tasker issue show <id> [OPTIONS]
```

**Arguments:**
- `<id>` — Issue ID (UUID)

**Options:**
- `--include-dependencies` — Show blocking relationships
- `--include-reasoning` — Show reasoning logs
- `--output json|table` — Output format

**Examples:**

```bash
# Basic
tasker issue show issue-550e8400-e29b-41d4-a716-446655440000

# With dependencies
tasker issue show issue-550e8400-e29b-41d4-a716-446655440000 --include-dependencies

# Full details
tasker issue show issue-550e8400-e29b-41d4-a716-446655440000 \
  --include-dependencies \
  --include-reasoning
```

---

### `tasker issue update`

Update issue details.

**Syntax:**
```bash
tasker issue update <id> [OPTIONS]
```

**Options:**
- `--title <text>` — New title
- `-s, --status <status>` — New status
- `-p, --priority <priority>` — New priority
- `--description <text>` — New description
- `--assignee <email>` — Reassign
- `--tags <tags>` — Update tags

**Examples:**

```bash
# Update status
tasker issue update issue-123 -s IN_PROGRESS

# Change priority
tasker issue update issue-123 -p CRITICAL

# Assign
tasker issue update issue-123 --assignee dev@example.com

# Multiple updates
tasker issue update issue-123 \
  -s IN_PROGRESS \
  -p HIGH \
  --assignee dev@example.com
```

---

### `tasker issue close`

Close an issue with resolution.

**Syntax:**
```bash
tasker issue close <id> [OPTIONS]
```

**Options:**
- `-r, --resolution <resolution>` — Resolution type (default: implemented)
- `--commit-sha <sha>` — Commit SHA that fixed it
- `--notes <text>` — Resolution notes

**Resolution types:**
- `implemented` — Issue was implemented
- `duplicate` — Issue is duplicate of another
- `wontfix` — Decided not to fix
- `external` — Fixed externally

**Examples:**

```bash
# Simple close
tasker issue close issue-123

# With commit reference
tasker issue close issue-123 --commit-sha abc123def456

# Mark as duplicate
tasker issue close issue-123 -r duplicate

# With notes
tasker issue close issue-123 -r implemented --notes "Fixed in PR #456"
```

---

### `tasker issue delete`

Delete an issue.

**Syntax:**
```bash
tasker issue delete <id> [OPTIONS]
```

**Options:**
- `--force` — Skip confirmation

**Examples:**

```bash
# Delete with confirmation
tasker issue delete issue-123

# Force delete
tasker issue delete issue-123 --force
```

---

## Dependency Management

### `tasker dependency add`

Create a blocking dependency.

**Syntax:**
```bash
tasker dependency add <issue> --depends-on <other_issue>
```

**Arguments:**
- `<issue>` — Issue that is blocked
- `--depends-on <other>` — Issue that blocks it

**Examples:**

```bash
# issue-123 is blocked by issue-456
tasker dependency add issue-123 --depends-on issue-456

# Multiple dependencies
tasker dependency add issue-123 --depends-on issue-456
tasker dependency add issue-123 --depends-on issue-789
```

---

### `tasker dependency remove`

Remove a blocking dependency.

**Syntax:**
```bash
tasker dependency remove <issue> --depends-on <other_issue>
```

**Examples:**

```bash
tasker dependency remove issue-123 --depends-on issue-456
```

---

### `tasker dependency list`

List dependencies for an issue.

**Syntax:**
```bash
tasker dependency list <issue> [OPTIONS]
```

**Options:**
- `--direction <in|out|both>` — Direction (default: both)
  - `in` — Issues that depend on this one
  - `out` — Issues this one depends on

**Examples:**

```bash
# What blocks this issue
tasker dependency list issue-123 --direction out

# What this issue blocks
tasker dependency list issue-123 --direction in

# All relationships
tasker dependency list issue-123
```

---

### `tasker dependency chain`

Trace the entire dependency chain for an issue.

**Syntax:**
```bash
tasker dependency chain <issue> [OPTIONS]
```

**Options:**
- `--depth <n>` — Maximum depth (default: unlimited)
- `--output json|tree` — Output format (default: tree)

**Examples:**

```bash
# View dependency tree
tasker dependency chain issue-123

# Limited depth
tasker dependency chain issue-123 --depth 3

# JSON format
tasker dependency chain issue-123 --output json
```

**Output:**
```
issue-123 (BLOCKED)
├─ blocked by: issue-456 (IN_PROGRESS)
│  └─ blocked by: issue-789 (OPEN)
│     └─ blocked by: issue-999 (RESOLVED)
└─ blocked by: issue-111 (CLOSED)
```

---

### `tasker dependency blocked`

Show all currently blocked issues.

**Syntax:**
```bash
tasker dependency blocked [OPTIONS]
```

**Options:**
- `--component <id|name>` — Filter by component
- `--priority <priority>` — Filter by priority
- `--output json|table` — Output format
- `--sort <field>` — Sort by field
- `--project, -p <project>` — Filter by project name (v1.0.5+)

**Examples:**

```bash
# All blocked issues
tasker dependency blocked

# In specific component
tasker dependency blocked --component auth-service

# High priority blocked
tasker dependency blocked --priority HIGH

# Sorted by priority
tasker dependency blocked --sort priority

# Filter by project (v1.0.5+)
tasker dependency blocked --project "My Project"
tasker dependency blocked -p "Blog Platform"
```

---

## Analysis Commands

### `tasker analyze root-cause`

Analyze root cause of an issue.

**Syntax:**
```bash
tasker analyze root-cause <issue> [OPTIONS]
```

**Options:**
- `--depth <n>` — Analysis depth
- `--include-code` — Include code references
- `--output json|text` — Output format

**Examples:**

```bash
tasker analyze root-cause issue-123
tasker analyze root-cause issue-123 --include-code --depth 3
```

---

### `tasker analyze impact`

Analyze potential impact of an issue.

**Syntax:**
```bash
tasker analyze impact <issue> [OPTIONS]
```

**Options:**
- `--affected-components` — Show affected components
- `--affected-issues` — Show affected issues
- `--affected-users` — Estimate user impact

**Examples:**

```bash
tasker analyze impact issue-123
tasker analyze impact issue-123 --affected-components --affected-issues
```

---

## Code-as-Graph Commands

### `tasker code-graph scan`

Scan codebase and update code graph.

**Syntax:**
```bash
tasker code-graph scan <path> [OPTIONS]
```

**Arguments:**
- `<path>` — Path to scan (. for current directory)

**Options:**
- `--language <lang>` — Programming language (auto-detect if omitted)
- `--incremental` — Only update changed files
- `--patterns <glob>` — File patterns to include
- `--exclude <glob>` — File patterns to exclude

**Languages Supported:**
- python, javascript, typescript, java, cpp, c

**Examples:**

```bash
# Scan current directory
tasker code-graph scan .

# Scan specific directory
tasker code-graph scan src/

# Specific language
tasker code-graph scan src/ --language python

# Incremental update
tasker code-graph scan src/ --incremental

# Custom patterns
tasker code-graph scan src/ \
  --patterns "**/*.py" \
  --exclude "**/test_*.py"
```

---

### `tasker code-graph find`

Find code symbols in the graph.

**Syntax:**
```bash
tasker code-graph find <symbol> [OPTIONS]
```

**Arguments:**
- `<symbol>` — Symbol name or pattern

**Options:**
- `--type <type>` — Symbol type (class, function, variable)
- `--file <path>` — Filter by file
- `--language <lang>` — Filter by language

**Examples:**

```bash
# Find all occurrences
tasker code-graph find MyClass

# Find function only
tasker code-graph find MyClass --type function

# In specific file
tasker code-graph find parse_config --file src/config.py
```

---

### `tasker code-graph calls`

Find all callers of a function.

**Syntax:**
```bash
tasker code-graph calls <function> [OPTIONS]
```

**Examples:**

```bash
tasker code-graph calls authenticate
tasker code-graph calls parse_config --include-indirect
```

---

## Information Commands

### `tasker init`

Initialize project configuration interactively.

**Syntax:**
```bash
tasker init [OPTIONS]
```

**Options:**
- `--mode <direct|api>` — Skip mode selection
- `--config <path>` — Config file path
- `--no-interactive` — Non-interactive mode

**Examples:**

```bash
# Interactive setup
tasker init

# Setup for API mode
tasker init --mode api

# Auto-configure
tasker init --mode direct \
  --neo4j-uri bolt://db.example.com:7687 \
  --neo4j-user admin
```

---

### `tasker status`

Show system status and configuration.

**Syntax:**
```bash
tasker status [OPTIONS]
```

**Options:**
- `--check-connectivity` — Verify database/API connection
- `--show-config` — Display active configuration

**Examples:**

```bash
# Basic status
tasker status

# Check connectivity
tasker status --check-connectivity

# Show config
tasker status --show-config
```

**Output:**
```
SocialSeed Tasker Status Report
================================
Version: 1.0.0
Mode: direct
Status: ✓ Connected

Database:
  URL: bolt://localhost:7687
  User: neo4j
  Status: ✓ Connected
  
Configuration loaded from:
  1. Environment variables (highest)
  2. .agent/configs/tasker.yml
  3. Built-in defaults

Last updated: 2026-05-25 10:30:00
```

---

### `tasker version`

Show Tasker version.

**Syntax:**
```bash
tasker version
```

**Output:**
```
SocialSeed Tasker version 1.0.0
```

---

### `tasker help`

Show help for all commands.

**Syntax:**
```bash
tasker help [command]
```

**Examples:**

```bash
# Overall help
tasker help

# Help for specific command
tasker help component

# Help for subcommand
tasker help issue create
```

---

## Global Options

Available on all commands:

```bash
tasker [GLOBAL_OPTIONS] <command>
```

| Option | Description |
|--------|-------------|
| `--help, -h` | Show help |
| `--version` | Show version |
| `--verbose, -v` | Verbose output |
| `--quiet, -q` | Suppress output |
| `--color, --no-color` | Color output (default: auto) |
| `--output, -o <format>` | Output format |
| `--config <path>` | Config file path |

**Examples:**

```bash
# Verbose mode
tasker -v component list

# Quiet mode
tasker -q component create test

# JSON output
tasker -o json component list

# Custom config
tasker --config ~/.tasker/config.yml component list
```

---

## Output Formats

### Table (default)

```bash
tasker component list
```

```
ID                                   NAME          PROJECT
550e8400-e29b-41d4-a716-446655440000 auth-service  backend
```

### JSON

```bash
tasker component list -o json
```

```json
{
  "components": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "auth-service",
      "project": "backend"
    }
  ]
}
```

### Text/CSV

```bash
tasker component list -o csv
```

```
id,name,project
550e8400-e29b-41d4-a716-446655440000,auth-service,backend
```

---

## Common Patterns

### Filter and Export

```bash
# High priority issues in JSON
tasker issue list -p HIGH -o json > high-priority.json

# All components in CSV
tasker component list -o csv > components.csv
```

### Dry Run

```bash
# Preview what will be created
tasker issue create "New issue" -c comp --dry-run

# Apply after reviewing
tasker issue create "New issue" -c comp
```

### Scripting

```bash
# Get issue ID and use it
ISSUE_ID=$(tasker issue create "Auto-created" -c comp -o json | jq -r '.id')
tasker dependency add $ISSUE_ID --depends-on other-issue
```

---

## Troubleshooting

### Issue: Command not found

```bash
# Ensure package is installed
pip install -e .

# Check virtual environment is activated
which tasker  # Should show path in .venv/
```

### Issue: Connection error

```bash
# Check mode and configuration
tasker status --check-connectivity

# Verify database/API is running
curl http://localhost:8000/health  # Neo4j
curl http://localhost:8888/health  # API
```

---

## See Also

- [Installation](./installation.md)
- [Configuration Reference](./configuration-reference.md)
- [Dual Mode Guide](./dual-mode-guide.md)
- [Troubleshooting](./troubleshooting.md)
