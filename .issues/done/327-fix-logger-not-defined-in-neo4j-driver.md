# Issue #327: NameError on 'logger' in neo4j_driver.py exception handler

## Description
In `infrastructure/neo4j_driver.py`, line 147 of the `_init_schema()` method, the exception handler calls `logger.debug(...)` but `logger` is not defined in the module scope. This causes a secondary crash after the primary CypherSyntaxError, obscuring the root cause.

## Expected Behavior
When a schema initialization command fails, a clear error message should be logged/displayed.

## Actual Behavior
```
NameError: name 'logger' is not defined
```

## Steps to Reproduce
1. Trigger schema initialization (any CLI command or API startup)
2. The CypherSyntaxError occurs (see #326)
3. The exception handler crashes with NameError instead of logging the error

## Status: PENDING

## Priority: HIGH

## Component
CORE — `src/socialseed_tasker/infrastructure/neo4j_driver.py` (line 147)

## Suggested Fix
Add a module-level logger definition, or replace `logger.debug()` with a `print()` or `logging` call.

## Impact
- Error messages are confusing and do not point to the root cause
- Prevents proper debugging of schema issues
