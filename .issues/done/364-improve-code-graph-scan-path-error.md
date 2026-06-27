# Issue #364: Code-graph scan path error lacks actionable suggestions

## Description
Running `tasker code-graph scan src` when the `src/` directory does not exist returns a bare error message: `Error scanning repository: Repository path does not exist: src`. It does not suggest valid paths, reference `--help`, or guide the user toward a solution. This hurts DX for new users.

## Expected Behavior
The error should include a suggestion, e.g.:
```
Error scanning repository: Repository path does not exist: src
Suggestion: Run from your project root or specify a valid path. Use 'tasker code-graph --help' for options.
```

## Actual Behavior
```
Error scanning repository: Repository path does not exist: src
```

## Steps to Reproduce
1. Run `tasker code-graph scan src` in a directory without `src/`
2. Observe the error output

## Status: PENDING

## Priority: LOW

## Component
CLI

## Suggested Fix
Add path validation with a helpful suggestion message. If the path doesn't exist, suggest common project directories or reference `--help`.

## Impact
Low. Minor DX improvement for new users learning the code-graph feature.
