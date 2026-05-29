# Issue #349: CLI --help Output Needs More Detailed Examples for Discovery

## Description
As a user who relies only on `--help` and error messages (Chaos Monkey profile), the CLI is intuitive enough to discover commands but lacks sufficient inline examples for complex operations like creating issues with specific parameters.

## Expected Behavior
`--help` output should include more detailed, contextual examples that guide users through common workflows without needing external documentation.

## Actual Behavior
The current `--help` shows basic examples but users need extensive trial and error to discover parameter combinations, especially for dependency management and filtering.

## Steps to Reproduce
1. Run `tasker --help`
2. Try creating an issue with `tasker issue create "title" --priority HIGH`
3. Try creating dependencies without reading docs

## Status: SOLVED

## Priority: LOW

## Component
CLI

## Suggested Fix
Add more comprehensive examples in the `--help` output for each subcommand, particularly for:
- `tasker issue create` with all parameters
- `tasker dependency add` with correct syntax
- `tasker issue list` with filter flags
- Common workflow patterns

## Impact
Reduces learning curve and improves DX for new users and AI agents.

## Fix
Enhanced --help output across the CLI:
- **Main `tasker --help`**: Added "Common Workflow" section with 6-step workflow pattern; enriched epilog examples with labels, --project filter, dependency chain
- **`tasker issue create --help`**: Added `ISSUE_CREATE_EPILOG` with 4 examples covering description, priority, labels, and enforce; added tips section for component lookup, priority values, labels syntax
- **`tasker issue list --help`**: Added `ISSUE_LIST_EPILOG` with 5 filter combos including --json output; enriched --status help with all valid values
- **`tasker dependency add --help`**: Enhanced `DEP_ADD_EPILOG` with --force example, positional vs explicit syntax clarification, and tips
