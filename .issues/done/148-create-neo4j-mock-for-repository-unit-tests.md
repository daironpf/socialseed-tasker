# Issue #148: Create Neo4j mock/fake driver for repository unit tests

## Description

The `storage/graph_database/repositories.py` file has only 19% code coverage (263 missing statements). Neo4j-specific queries cannot be unit tested without a mock driver. Create a FakeNeo4jDriver for unit testing.

### Current State

- `repositories.py`: 325 statements, 62 covered, 263 missing (19% coverage)
- All repository methods interact with Neo4j driver directly
- Integration tests require actual Neo4j (currently failing)

### Requirements

1. Create `tests/fakes/fake_neo4j_driver.py` with in-memory graph simulation
2. Support all Neo4j query patterns used in repositories
3. Allow test setup of nodes and relationships
4. Support transactions and session management

### Technical Details

Create fake driver that mirrors the driver interface:

```python
# tests/fakes/fake_neo4j_driver.py
class FakeNeo4jDriver:
    """In-memory Neo4j replacement for unit tests."""
    
    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.relationships: list[dict] = []
    
    @asynccontextmanager
    async def session(self):
        yield FakeSession(self)
    
    async def verify_connectivity(self):
        return True

class FakeSession:
    def __init__(self, driver):
        self.driver = driver
        self._transactions = []
    
    async def run(self, query: str, **params):
        # Parse Cypher query and return mock results
        pass
```

### Usage

```python
# tests/unit/test_repositories.py
class TestIssueRepository:
    @pytest.fixture
    def fake_driver(self):
        driver = FakeNeo4jDriver()
        driver.add_node("Issue", {"id": "123", "title": "Test"})
        return driver
    
    def test_get_issue(self, fake_driver):
        repo = Neo4jIssueRepository(fake_driver)
        issue = repo.get_issue("123")
        assert issue is not None
```

## Status: COMPLETED