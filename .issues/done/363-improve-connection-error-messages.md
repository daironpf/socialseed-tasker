# Issue #363: Connection error exposes internal IP resolution details

## Description
When Neo4j is unreachable (e.g., database container stopped), the CLI error message exposes internal implementation details including `ResolvedIPv6Address`, `ResolvedIPv4Address`, port numbers, and Windows error codes. While functional and the exit code is correct (1), the verbosity may confuse end users and exposes internal network resolution internals.

## Expected Behavior
A clean, user-friendly error message such as:
```
[ERROR]: Cannot connect to Neo4j at localhost:7687. Is the database running?
```

## Actual Behavior
```
Error: Couldn't connect to localhost:7687 (resolved to ('[::1]:7687', '127.0.0.1:7687')):
Failed to establish connection to ResolvedIPv6Address(('::1', 7687, 0, 0)) (reason [WinError 10061])
Failed to establish connection to ResolvedIPv4Address(('127.0.0.1', 7687)) (reason [WinError 10061])
```

## Steps to Reproduce
1. Run `docker compose stop tasker-db`
2. Run `tasker issue list`
3. Observe the error output

## Status: PENDING

## Priority: LOW

## Component
CLI

## Suggested Fix
Wrap the Neo4j connection error in a try/except block that catches `ServiceUnavailable` or connection errors and returns a simplified user-friendly message. Preserve the full error in debug/log level for troubleshooting.

## Impact
Low. Error is clear enough but exposes internal details and looks unpolished.
