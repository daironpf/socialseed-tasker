# Issue #345: tasker init uses Rich Prompt which cannot be automated via stdin

## Description
`tasker init` uses `rich.prompt.Prompt.ask()` for all user input, which reads directly from the terminal (TTY). Piping input via PowerShell/cmd fails with EOFError. This prevents automation of project initialization in CI or headless environments.

## Expected Behavior
Should support a `--non-interactive` mode with CLI flags for all options, or fall back to `input()` when stdin is not a TTY.

## Actual Behavior
Piping "Blog Platform\n2\n\n\n" to `tasker init` resulted in `EOFError: EOF when reading a line`.

## Steps to Reproduce
1. Run: `echo "Blog Platform" | tasker init`
2. Observe EOFError

## Status: PENDING

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Support `--non-interactive` mode with CLI flags for all options, or detect non-TTY stdin and fall back to `input()`.

## Impact
Cannot automate `tasker init` in CI/CD pipelines or scripted environments.

## Related Issues
- FIND-004 from black-box evaluation 2026-05-28
