# Issue #34: Increase Code Coverage to 80%

## Description

Current test coverage is 68%. The project should aim for 80% coverage to ensure better quality and catch regressions.

### Requirements

- Analyze uncovered lines in coverage report
- Add tests for:
  - Storage layer (file_store.py - 0% coverage currently)
  - Graph database queries and repositories (0% coverage)
  - Remaining CLI commands not tested
  - API routes not fully tested
  - Core actions not tested
- Set coverage target in CI

### Technical Details

Files to focus on:
- `src/socialseed_tasker/storage/local_files/file_store.py` - 42 statements, 0% coverage
- `src/socialseed_tasker/storage/graph_database/driver.py` - 65 statements, 0% coverage  
- `src/socialseed_tasker/storage/graph_database/repositories.py` - 91 statements, 0% coverage
- `src/socialseed_tasker/entrypoints/cli/init_command.py` - 59 statements, 0% coverage
- `src/socialseed_tasker/entrypoints/terminal_cli/commands.py` - 277 statements, 51% coverage

### Business Value

Higher coverage = fewer bugs in production. 80% is a standard industry target.

## STATUS: COMPLETED