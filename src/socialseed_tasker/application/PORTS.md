# Application Ports

This document describes every **port** (Protocol interface) defined in `ports.py`.
Each port is the canonical contract between the application layer and an
external adapter in the infrastructure layer.

---

## GraphPort

**Purpose:** Persist and query graph data (nodes, relationships).

### Methods

```python
def create_node(label: str, properties: dict[str, Any]) -> str
```
- **Input:** `label="Issue"`, `properties={"title": "Fix login"}`
- **Output:** `"node-uuid-123"`

```python
def get_node(node_id: str) -> Optional[NodeRecord]
```
- **Input:** `"node-uuid-123"`
- **Output:** `NodeRecord(id="node-uuid-123", labels=["Issue"], properties={...})` or `None`

```python
def run_cypher(query: str, params: Optional[dict[str, Any]] = None) -> QueryResult
```
- **Input:** `"MATCH (n:Issue {id: $id}) RETURN n"`, `{"id": "abc"}`
- **Output:** `QueryResult(records=[{"n": {...}}])`

```python
def delete_node(node_id: str) -> None
```
- **Input:** `"node-uuid-123"`

### Exceptions
- `GraphPortError` — on connection failure, timeout, or constraint violation.

---

## ParserPort

**Purpose:** Parse source code and extract structural information.

### Methods

```python
def parse_file(path: str) -> dict[str, Any]
```
- **Input:** `"/src/main.py"`
- **Output:** `{"type": "module", "body": [...], "errors": []}`

```python
def extract_symbols(ast: dict[str, Any]) -> list[dict[str, Any]]
```
- **Input:** `{"type": "module", "body": [...]}`
- **Output:** `[{"name": "UserService", "kind": "class", "line": 10}, ...]`

```python
def extract_imports(ast: dict[str, Any]) -> list[str]
```
- **Input:** `{"type": "module", "body": [...]}`
- **Output:** `["os", "django.db.models", ...]`

### Exceptions
- `ParserError` — file not found, encoding error, or syntax error.

---

## GitPort

**Purpose:** Read-only Git operations for repository analysis.

### Methods

```python
def list_changed_files(ref: str) -> list[str]
```
- **Input:** `"abc123def"`
- **Output:** `["src/main.py", "tests/test_main.py"]`

```python
def read_file_at_ref(path: str, ref: str) -> str
```
- **Input:** `"src/main.py"`, `"abc123def"`
- **Output:** `"def hello():\\n    print('hello')\\n"`

```python
def current_branch() -> str
```
- **Output:** `"feature/my-branch"`

### Exceptions
- `GitError` — ref not found, file not in commit, or repository not accessible.

---

## EmbeddingPort

**Purpose:** Generate vector embeddings from text.

### Methods

```python
def embed_text(text: str) -> list[float]
```
- **Input:** `"refactor user authentication"`
- **Output:** `[0.012, -0.034, ..., 0.098]` (fixed-length vector)

```python
def embed_batch(texts: list[str]) -> list[list[float]]
```
- **Input:** `["fix login", "add tests"]`
- **Output:** `[[0.01, ...], [0.02, ...]]` (same order)

### Exceptions
- `EmbeddingError` — API failure, rate limit, or invalid input.

---

## StoragePort

**Purpose:** Generic key-value cache / artifact store.

### Methods

```python
def put(key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None
```
- **Input:** `"embedding:issue-123"`, `b"..."`, `ttl_seconds=3600`

```python
def get(key: str) -> Optional[bytes]
```
- **Input:** `"embedding:issue-123"`
- **Output:** `b"..."` or `None`

```python
def delete(key: str) -> None
```
- **Input:** `"embedding:issue-123"`

### Exceptions
- `StorageError` — backend unavailable, full, or permission denied.

---

## LoggerPort

**Purpose:** Structured logging from application code.

### Methods

```python
def info(message: str, **fields: Any) -> None
```
- **Input:** `"issue created"`, `issue_id="abc"`, `elapsed_ms=42`

```python
def debug(message: str, **fields: Any) -> None
```

```python
def warning(message: str, **fields: Any) -> None
```

```python
def error(message: str, **fields: Any) -> None
```

### Exceptions
None (implementations must not raise).
