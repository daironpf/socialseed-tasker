# Issue #111: Increase Integration Test Coverage

## Description

The current test coverage is 51% overall, with some modules at 100% but others with significant gaps. Integration tests that verify actual Neo4j connectivity and end-to-end workflows are needed.

## Requirements

- Add integration tests for all main API endpoints with real Neo4j
- Add tests for dependency chains (create, list, delete)
- Add tests for analysis features (root cause, impact)
- Add tests for close issue with dependencies
- Increase overall test coverage to 70%+
- Add Docker-based test suite for CI/CD

## Technical Details

### Current Coverage Gaps
```
entrypoints/terminal_cli/commands.py: 23%
storage/graph_database/repositories.py: 0%
entrypoints/web_api/routes.py: 31%
bootstrap/container.py: 67%
```

### Integration Tests Needed

1. **Full CRUD operations with Neo4j**
   - Create component → Get component → Update component → Delete component

2. **Dependency management**
   - Create issue A, Create issue B
   - Add dependency A → B
   - List dependencies for A
   - Try circular dependency (should fail)
   - Close issue A (should fail - has dependent)

3. **Analysis features**
   - Create multiple issues with dependencies
   - Run impact analysis on issue
   - Run root cause analysis
   - Verify results in Neo4j

4. **API with real repository**
   - Test all endpoints with Neo4jRepository instead of MockRepository

### Implementation Location
```
tests/integration/
├── test_api_neo4j.py
├── test_cli_neo4j.py
├── test_analysis.py
└── conftest.py  # Docker containers for testing
```

## Business Value

- Confirms all features work end-to-end
- Prevents regressions
- Increases confidence in deployments

## Status: COMPLETED