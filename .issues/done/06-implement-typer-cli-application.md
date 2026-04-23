# Issue #06: Implement Typer-Based CLI Application

## Description

Build the terminal CLI entrypoint in `src/socialseed_tasker/entrypoints/terminal_cli/` using **Typer** and **Rich** for professional terminal output. This CLI is the primary human interface to the socialseed-tasker system.

### Requirements

#### CLI Structure

**`app.py`** - Main Typer application
- Create the main `typer.Typer()` instance
- Configure Rich text rendering for all output
- Register all command groups
- Set up proper error handling with Rich tracebacks

**`commands.py`** - CLI commands organized in groups

#### Required Command Groups

**`issue` commands:**
- `issue create` - Create a new issue with title, description, component, priority, labels
- `issue list` - List issues with optional filters (status, component, labels)
- `issue show <id>` - Show detailed issue information including dependencies
- `issue close <id>` - Close an issue (validates no open dependencies)
- `issue move <id> --to <component>` - Move issue to another component
- `issue delete <id>` - Delete an issue (with confirmation prompt)

**`dependency` commands:**
- `dependency add <issue_id> <depends_on_id>` - Add [:DEPENDS_ON] relationship
- `dependency remove <issue_id> <depends_on_id>` - Remove [:DEPENDS_ON] relationship
- `dependency list <issue_id>` - List all dependencies and dependents
- `dependency chain <issue_id>` - Show full transitive dependency chain
- `dependency blocked` - Show all issues blocked by open dependencies

**`component` commands:**
- `component create` - Create a new component
- `component list` - List all components
- `component show <id>` - Show component details and its issues

#### Output Requirements
- Use **Rich tables** for list views
- Use **Rich panels/cards** for detailed issue views
- Color-code status (OPEN=green, IN_PROGRESS=yellow, CLOSED=blue, BLOCKED=red)
- Color-code priority (LOW=dim, MEDIUM=normal, HIGH=bright, CRITICAL=bright+bold)
- Show dependency graphs using ASCII art or tree structures
- Progress indicators for long-running operations
- Confirmation prompts for destructive operations (delete, close)

#### Error Handling
- User-friendly error messages (not stack traces)
- Validation errors with clear guidance on what went wrong
- Connection errors with troubleshooting hints
- Exit codes: 0=success, 1=error, 2=validation error

### Requirements
- All CLI code goes in `entrypoints/terminal_cli/`
- Must use dependency injection to get repository from bootstrap container
- No business logic in CLI - delegate to core actions
- Support `--help` on all commands and subcommands
- Support `--json` flag on list commands for machine-readable output

### Business Value

The CLI provides the primary human interface to the task management system. Rich output makes complex graph relationships (dependencies, blocks, affects) visually comprehensible in a terminal environment. The `--json` flag enables scripting and integration with other tools.

## Status: COMPLETED
