# Issue #416: Config path uses Windows backslashes instead of forward slashes

## Description
The config path displayed in `tasker status` uses Windows-native backslashes:
```
Config: D:\.dev\proyectos\socialseed-tasker\real-test\.agent\configs\tasker.yml
```
These paths may break cross-platform scripts, Docker volume mounts, and documentation that expects POSIX-style forward slashes.

## Expected Behavior
Paths should be normalized to use forward slashes (`/`) for cross-platform compatibility, especially when displayed in status output or stored in configuration files.

## Actual Behavior
Raw Windows paths with backslashes are displayed and potentially stored.

## Steps to Reproduce
1. Run `tasker status` on Windows
2. Observe the `Config:` line uses `\` separators

## Status: RESOLVED

## Priority: LOW

## Component
CLI — config path resolution

## Suggested Fix
Normalize the config path using `Path.as_posix()` when displaying in status output:
```python
config_path_str = str(config_path).replace("\\", "/")
# or use PureWindowsPath(config_path).as_posix()
```

## Impact
Low — cosmetic on Windows, but can break scripts and Docker commands on Unix.

## Related Issues
- (none)

## Changes Made
Normalized the config path in `tasker status` display using `Path.as_posix()` in `src/socialseed_tasker/cli/commands/status_commands.py:99`:
```python
# Before
f"[bold]Config:[/bold] {cfg_path or '(none)'}\n"
# After
f"[bold]Config:[/bold] {cfg_path.as_posix() if cfg_path else '(none)'}\n"
```

## Verification
On Windows, `tasker status` shows `Config: D:/.dev/proyectos/...` (forward slashes) instead of `Config: D:\.dev\proyectos\...` (backslashes).
