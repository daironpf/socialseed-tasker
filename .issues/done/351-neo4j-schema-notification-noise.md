# Issue #351: Neo4j Schema Notification Noise Floods CLI Output

## Description
Every CLI command that connects to Neo4j prints 30+ INFO-level notifications about indexes and constraints already existing. These messages come from `neo4j.notifications` logger and show `GqlStatusObject` entries like "index or constraint already exists" for every index/constraint in the schema. The noise makes actual command output impossible to read without filtering.

This finding was discovered during a black-box evaluation (see `real-test/report.md`).

## Expected Behavior
CLI commands should only print meaningful output (issue details, lists, error messages). Neo4j schema notifications should be suppressed or logged only at DEBUG level.

## Actual Behavior
Every command produces ~40 lines of JSON like this before any real output:
```json
{"timestamp": "...", "level": "INFO", "logger": "neo4j.notifications",
 "message": "Received notification from DBMS server: <GqlStatusObject ... 'index or constraint already exists' ...>"}
```

## Steps to Reproduce
1. Install and configure tasker
2. Run any command: `tasker issue list`, `tasker issue create`, `tasker status`
3. Observe the wall of Neo4j notification JSON before the actual output
4. Note there are ~35 separate notifications per command

## Status: PENDING

## Priority: MEDIUM

## Component
CORE

## Suggested Fix
1. Configure the `neo4j.notifications` Python logger to suppress INFO-level messages:
   ```python
   import logging
   logging.getLogger("neo4j.notifications").setLevel(logging.WARNING)
   ```
2. Alternatively, set the `notifications_min_level` parameter in the Neo4j driver configuration to `WARNING` level.
3. Verify that actual Neo4j errors (WARNING+) are still surfaced.

## Impact
Severe DX degradation. CLI output is cluttered, making it hard to read results and error messages. New users may think the tool is broken or overly verbose.

## Related Issues
- FIND-001 (report.md)
