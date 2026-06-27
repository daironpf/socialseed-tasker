# Issue #375: Config file discovery finds parent project config before nested project

## Description
`mode_config.py:_discover_config_file()` searches upward from CWD through parent directories. When running Tasker from a subdirectory that is inside another Tasker project, the parent's `.agent/configs/tasker.yml` is found first, causing mode/connection misconfiguration.

## Expected Behavior
A project in a subdirectory should find its own `.agent/configs/tasker.yml` before any parent's config. The discovery should prefer the closest match (starting from CWD and stopping at the first found).

## Actual Behavior
Running from `real-test/` (a subdirectory of the main project) loads the parent's config at `D:\.dev\proyectos\socialseed-tasker\.agent\configs\tasker.yml` instead of `real-test\.agent\configs\tasker.yml`.

## Steps to Reproduce
1. Create a Tasker project at `/parent/`
2. Inside it, create a nested Tasker project at `/parent/nested/`
3. Run `tasker component list` from `/parent/nested/`
4. Observe it uses `/parent/.agent/configs/tasker.yml` config

## Status: COMPLETED

## Priority: MEDIUM

## Component
CLI, Configuration

## Suggested Fix
1. First search from CWD looking for `.agent/configs/tasker.yml`
2. Only if not found, search upward through parents
3. OR: allow explicit `TASKER_CONFIG_PATH` env var override

## Impact
Users with multiple Tasker projects nested within each other (common in monorepos) get silent misconfiguration. Workaround exists via `TASKER_MODE` env var but is not discoverable.

## Related Issues
- (none)
