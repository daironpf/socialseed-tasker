# Issue #389: `tasker code-graph scan . --incremental` reports 0 files, 0 symbols

## Description
Running `tasker code-graph scan . --incremental` from the project root returns "Found 0 files, 0 symbols, 0 imports", even though the directory contains hundreds of Python source files. The scan appears to not traverse the filesystem correctly.

## Expected Behavior
The code-graph scan should discover all Python source files in the project and extract symbols, imports, and dependencies.

## Actual Behavior
```
$ tasker code-graph scan . --incremental
Scanning repository: .
Found 0 files, 0 symbols, 0 imports
Saved to graph via API
```

## Steps to Reproduce
1. Navigate to the project root
2. `tasker code-graph scan . --incremental`
3. Observe zero results despite source files existing

## Status: PENDING

## Priority: LOW
