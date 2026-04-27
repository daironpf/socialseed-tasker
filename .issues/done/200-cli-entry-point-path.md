# Issue #200 - CLI Entry Point Not in PATH After Installation

## Description

After running `pip install -e .` or `pip install .`, the `tasker` CLI command is not immediately available in bash shell. The install outputs a warning about Scripts not in PATH, and users must find alternative ways to invoke the CLI.

## Status: COMPLETED

## Priority

**MEDIUM** - Affects new user onboarding

## Component

CLI, Installation, Documentation

## Changes Made

### Updated README.md

Added comprehensive "Installation" section with:

1. **Prerequisites** - Python 3.10+, Neo4j 5.x, pip

2. **Install via pip** - Standard installation from PyPI

3. **Install via git (Development)** - Editable mode installation

4. **Command Not Found?** section with platform-specific solutions:
   - Windows PowerShell
   - Windows CMD
   - Linux/Mac

5. **Alternative: Use Python Module Directly**:
   ```bash
   python -m socialseed_tasker.entrypoints.terminal_cli.app --help
   python -m socialseed_tasker.entrypoints.web_api
   ```

6. **Verify Installation** - How to check CLI and API installation

## Verification

```bash
$ python -m ruff check src/
All checks passed!
```

## Impact

New users now have clear installation instructions:
- Clear PATH instructions for each platform
- Documented alternative `python -m` invocation
- Verification steps included

## Related Issues

- Real-Test Evaluation: FIND-002