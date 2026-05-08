# Issue #261: Implement Commit Repository

## Description

According to the Graph Data Model (GraphDataModelDetails.md), the **Commit** node represents a physical change in the repository's version control history. It acts as the ultimate proof of work, linking the high-level reasoning of an agent to the low-level modifications of the source code.

### Current State

The `Commit` entity already exists in `core/task_management/entities.py` with all required properties:
- `sha` (String, Primary identifier - 40 char Git hash)
- `message` (String)
- `authorName` (String)
- `authorEmail` (String)
- `timestamp` (DateTime)
- `isAiGenerated` (Boolean)
- `branch` (String)
- `additions` (Integer)
- `deletions` (Integer)
- `filesChanged` (Integer)

However, there is **no dedicated CommitRepository** in `storage/graph_database/` to perform CRUD operations and link commits to the graph relationships.

### Requirements

#### Create `storage/graph_database/commit_repository.py`

Implement a `CommitRepository` class with the following methods:

```python
class CommitRepository:
    def create_commit(self, commit: Commit) -> None:
        """Create a new Commit node in Neo4j."""
    
    def get_commit(self, sha: str) -> Commit | None:
        """Get a commit by SHA hash."""
    
    def list_commits(
        self,
        branch: str | None = None,
        author: str | None = None,
        is_ai_generated: bool | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 50,
    ) -> list[Commit]:
        """List commits with optional filters."""
    
    def link_commit_to_agent(self, sha: str, agent_id: str) -> None:
        """Create (Agent)-[:AUTHORED]->(Commit) relationship."""
    
    def link_commit_to_user(self, sha: str, user_id: str) -> None:
        """Create (User)-[:AUTHORED]->(Commit) relationship."""
    
    def link_commit_to_issue(self, sha: str, issue_id: str) -> None:
        """Create (Issue)-[:RESOLVED_BY]->(Commit) relationship."""
    
    def link_commit_to_file(self, sha: str, file_path: str, change_type: str) -> None:
        """Create (Commit)-[:MODIFIED {type: "ADDED"|"MODIFIED"|"DELETED"}]->(CodeFile) relationship."""
    
    def link_commit_to_reasoning(self, sha: str, reasoning_id: str) -> None:
        """Create (ReasoningNode)-[:RESULTED_IN]->(Commit) relationship."""
    
    def get_commits_for_issue(self, issue_id: str) -> list[Commit]:
        """Get all commits that resolved an issue."""
    
    def get_commits_for_file(self, file_path: str, limit: int = 20) -> list[Commit]:
        """Get commit history for a file."""
    
    def get_author_stats(self, since: datetime | None = None) -> dict:
        """Get commit statistics by author (human vs AI)."""
    
    def delete_commit(self, sha: str) -> None:
        """Delete a commit from Neo4j."""
```

#### Add Commit Queries in `queries.py`

```cypher
CREATE_COMMIT = """..."""
GET_COMMIT = """..."""
LIST_COMMITS = """..."""
LINK_COMMIT_TO_AGENT = """..."""
LINK_COMMIT_TO_USER = """..."""
LINK_COMMIT_TO_ISSUE = """..."""
LINK_COMMIT_TO_FILE = """..."""
GET_COMMITS_FOR_ISSUE = """..."""
GET_COMMITS_FOR_FILE = """..."""
GET_AUTHOR_STATS = """..."""
```

#### Implement API Endpoints

Add to `routes.py`:
- `POST /api/v1/commits` - Record a new commit
- `GET /api/v1/commits/{sha}` - Get commit by SHA
- `GET /api/v1/commits` - List commits (with filters)
- `POST /api/v1/commits/{sha}/link/agent/{agent_id}` - Link commit to agent
- `POST /api/v1/commits/{sha}/link/user/{user_id}` - Link commit to user
- `POST /api/v1/commits/{sha}/link/issue/{issue_id}` - Link commit to issue (mark as resolved)
- `GET /api/v1/commits/issue/{issue_id}` - Get commits that resolved an issue
- `GET /api/v1/commits/file/{file_path}` - Get commit history for a file
- `GET /api/v1/commits/stats` - Get author statistics

#### Relationships to Implement (from model)

The Commit node has these key relationships:
- **(Agent)-[:AUTHORED]->(Commit):** Attributes change to AI Agent
- **(User)-[:AUTHORED]->(Commit):** Attributes change to human user
- **(Commit)-[:MODIFIED {type: "Enum"}]->(CodeFile):** Connects to files changed
- **(Commit)-[:PARENT_OF]->(Commit):** Git tree history
- **(ReasoningNode)-[:RESULTED_IN]->(Commit):** Links logic to implementation
- **(Issue)-[:RESOLVED_BY]->(Commit):** Indicates which change satisfied requirement

### Business Value

The Commit node enables:
1. **Full audit trail** - Trace every code change to its author (human or AI)
2. **AI productivity reporting** - `isAiGenerated` flag enables "AI vs Human" metrics
3. **Causal traceability** - Link reasoning to implementation through RESULTED_IN
4. **Issue resolution tracking** - Know exactly what code resolved an issue

## Status: COMPLETED

## Priority: MEDIUM