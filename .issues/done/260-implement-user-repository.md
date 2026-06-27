# Issue #260: Implement User Repository (CRUD)

## Description

According to the Graph Data Model (GraphDataModelDetails.md), the **User** node represents the human architect, lead developer, or project owner. It is essential for tracking responsibility and providing manual oversight for AI-generated decisions.

### Current State

The `User` entity already exists in `core/task_management/entities.py` with all required properties:
- `id` (UUID)
- `username` (String)
- `email` (String)
- `role` (Enum: ADMIN, LEAD_ARCHITECT, DEVELOPER, VIEWER)
- `githubHandle` (String)
- `createdAt` (DateTime)
- `lastLogin` (DateTime)
- `preferences` (JSON/String)

However, there is **no dedicated UserRepository** in `storage/graph_database/` to perform CRUD operations.

### Requirements

#### Create `storage/graph_database/user_repository.py`

Implement a `UserRepository` class with the following methods:

```python
class UserRepository:
    def create_user(self, user: User) -> None:
        """Create a new User node in Neo4j."""
    
    def get_user(self, user_id: str) -> User | None:
        """Get a user by ID."""
    
    def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email address."""
    
    def get_user_by_username(self, username: str) -> User | None:
        """Get a user by username."""
    
    def update_user(self, user_id: str, updates: dict) -> User:
        """Update user properties."""
    
    def delete_user(self, user_id: str) -> None:
        """Delete a user from Neo4j."""
    
    def list_users(self, role: str | None = None, limit: int = 50) -> list[User]:
        """List users, optionally filtered by role."""
    
    def update_last_login(self, user_id: str) -> None:
        """Update the last login timestamp."""
```

#### Add User Queries in `queries.py`

```cypher
CREATE_USER = """..."""
GET_USER = """..."""
GET_USER_BY_EMAIL = """..."""
GET_USER_BY_USERNAME = """..."""
UPDATE_USER = """..."""
DELETE_USER = """..."""
LIST_USERS = """..."""
UPDATE_LAST_LOGIN = """..."""
```

#### Implement API Endpoints

Add to `routes.py`:
- `POST /api/v1/users` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `GET /api/v1/users/email/{email}` - Get user by email
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user
- `GET /api/v1/users` - List users (with optional role filter)

#### Relationships to Implement

According to the model, the User node has these relationships:
- **(User)-[:VALIDATES {approved: Boolean, comment: String}]->(ReasoningNode):** Human reviews AI reasoning
- **(User)-[:MANAGES]->(Project):** Administrative ownership
- **(User)-[:ASSIGNED_TO]->(Issue):** Human tasks
- **(User)-[:AUTHORED]->(Commit):** Human code contributions

These relationships should be implemented through the repository methods.

### Business Value

The User node is critical for:
1. **Human-in-the-Loop (HITL) governance** - Track who validates agent decisions
2. **Audit trails** - Attribute code changes to humans vs AI
3. **Responsibility tracking** - Who owns which issues and projects

## Status: COMPLETED

## Priority: MEDIUM