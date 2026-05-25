# Issue #326: Schema initialization crashes with CypherSyntaxError on DEPENDS_ON index

## Description
The `_init_schema()` method in `infrastructure/neo4j_driver.py` contains an invalid Cypher query that causes the entire application (both CLI and API) to crash on startup. Every `tasker` command or `tasker serve` call fails.

## Expected Behavior
- CLI commands should work normally
- `tasker serve` should start the API server
- Schema initialization should handle all Neo4j indexes gracefully

## Actual Behavior
Every operation fails with:
```
neo4j.exceptions.CypherSyntaxError:
Invalid input 'i': expected ')'
"CREATE INDEX code_depends IF NOT EXISTS FOR ()-[r:DEPENDS_ON]->(i:Issue) ON (i.timestamp)"
```

Additionally, when the error is caught, a secondary `NameError: name 'logger' is not defined` occurs because the exception handler references an undefined `logger` variable.

## Steps to Reproduce
1. Start Neo4j
2. Run any CLI command: `tasker --help`
3. Observe CypherSyntaxError crash

## Status: PENDING

## Priority: CRITICAL

## Component
CORE — `src/socialseed_tasker/infrastructure/neo4j_driver.py` (`_init_schema` method)

## Suggested Fix
Change the Cypher query on the DEPENDS_ON relationship index from:
```cypher
CREATE INDEX code_depends IF NOT EXISTS FOR ()-[r:DEPENDS_ON]->(i:Issue) ON (i.timestamp)
```
to:
```cypher
CREATE INDEX code_depends IF NOT EXISTS FOR ()-[r:DEPENDS_ON]->() ON (r.timestamp)
```

## Impact
- **Blocking**: All CLI commands and the API server are completely non-functional
- **Affected Features**: Every feature that requires Neo4j access
- **Workaround Available**: Manually create the index with correct syntax, then restart. Or use `cypher-shell` to create it first.
