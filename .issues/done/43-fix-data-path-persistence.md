# Issue #43: Fix data path persistence across CLI commands

## Description

When creating a component in the temporary test directory with `TASKER_FILE_PATH="./data"`, subsequent commands using a different invocation style (e.g., without the environment variable prefix) may not find the component if the default path differs.

The issue is that the CLI doesn't properly handle the data path consistency across commands. When running from `temp_test_socialseed/`, components created in `data/` subdirectory cannot be found when using just `tasker component show <id>` because the default path resolves differently.

### Requirements

- Ensure consistent data path resolution across all CLI commands
- Make the `--backend` option and `TASKER_STORAGE_BACKEND` env var work together properly
- Add validation that warns when data path inconsistency is detected

### Technical Details

From the tests:
- Created component with `TASKER_FILE_PATH="./data"` → stored in `temp_test_socialseed/data/components/`
- First `tasker component list` showed old data from project root `.tasker-data/`
- Had to explicitly use `TASKER_FILE_PATH="./data"` for each command

The CLI container is initialized with `Container.from_env()` which reads from environment variables at startup, but the `--backend` option modifies `os.environ` after the container is created.

### Solution

1. Make the CLI container re-read configuration when options are changed
2. Or use a config file approach that persists the path setting
3. Add a `--data-path` or `--file-path` CLI option for explicit control

**Resolution**: Added `--file-path/-f` option to the main CLI callback that sets `TASKER_FILE_PATH` environment variable before the container is created. This ensures the file path is consistent across all commands in the same session.

## Status: COMPLETED