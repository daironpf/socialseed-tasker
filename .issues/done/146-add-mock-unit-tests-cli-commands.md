# Issue #146: Add mock-based unit tests for CLI commands

## Description

The `entrypoints/terminal_cli/commands.py` file has only 25% code coverage (648 missing statements). CLI commands need comprehensive unit tests using mocks to improve coverage and ensure reliability.

### Current State

- `commands.py`: 868 statements, 220 covered, 648 missing (25% coverage)
- All CLI commands are functional but not unit tested with mocks
- Tests require actual Neo4j connection or skip if unavailable

### Requirements

1. Add mock-based unit tests for all CLI commands using `unittest.mock`
2. Mock the repository layer to isolate CLI logic from storage
3. Test both success and error paths for each command
4. Test argument parsing and validation
5. Test output formatting (Rich console output)

### Target Commands to Test

- `tasker component create/list/show/update/delete`
- `tasker issue create/list/show/close/move/delete/start/finish`
- `tasker dependency add/list/chain/blocked`
- `tasker analyze root-cause/impact`
- `tasker init`
- `tasker seed run`

### Technical Details

Create `tests/unit/test_commands.py` with mock repositories:

```python
from unittest.mock import AsyncMock, MagicMock, patch

class TestComponentCommands:
    @patch("tasker.component.list")
    def test_component_list_success(self, mock_list):
        # Test listing components with mock repo
        pass
    
    @patch("tasker.component.create")
    def test_component_create_with_flags(self, mock_create):
        # Test create with -n, -d, -p flags
        pass
```

## Status: COMPLETED