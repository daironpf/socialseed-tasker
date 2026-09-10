# Issue #002 - Interactive Input Piping Issues in tasker init

## Description

`tasker init` doesn't handle piped input correctly, requiring manual file configuration. This prevents automated testing and CI/CD integration where interactive prompts cannot be answered.

## Expected Behavior

`tasker init` should accept parameters via command-line flags or pipe input to complete initialization without user interaction.

## Actual Behavior

```bash
$ echo "y\necommerce\n2\n" | tasker init .
# Fails with "Invalid option" or hangs waiting for input
```

The CLI doesn't properly read from stdin when input is piped, requiring manual intervention.

## Steps to Reproduce

1. Create a test directory with `git init`
2. Try to pipe input to `tasker init`:
   ```bash
   echo -e "y\necommerce\n2" | tasker init .
   ```
3. Observe that the CLI doesn't read the piped input correctly

## Root Cause

The CLI uses `input()` or similar interactive prompts that don't work well with piped stdin. Typer's interactive mode requires special handling for non-interactive use cases.

## Affected Files

- `src/socialseed_tasker/entrypoints/cli/init_command.py`
- `src/socialseed_tasker/core/system_init/interactive_init.py`

## Suggested Fix

1. **Add `--non-interactive` flag** with parameter passing:
   ```bash
   tasker init . --non-interactive --project-name "ecommerce" --mode api
   ```

2. **Or use `--config-file`** option:
   ```bash
   tasker init . --config-file init-config.json
   ```

3. **Or detect piped input** and switch to non-interactive mode automatically

## Impact

Prevents automated testing and CI/CD integration. Users must manually configure `tasker.yml` after scaffold when they can't use interactive mode.

## Priority: MEDIUM

## Component: CLI

## Status: COMPLETED

## Resolution

Added `--project-name` and `--mode` parameters to `interactive_init_command()`:
- `--project-name` / `-pn`: Sets project name without prompting
- `--mode` / `-m`: Sets connection mode (direct/api/full) without prompting
- Combined with `--yes` flag, enables fully non-interactive initialization

The function now detects when parameters are provided via CLI and skips the interactive menu.

## Verification

```bash
$ tasker init . --project-name "my-store" --mode api --yes
# Non-interactive mode: project=my-store, mode=api
# Successfully completes without prompting
```
