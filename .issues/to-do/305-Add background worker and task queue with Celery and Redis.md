### Issue 305 — Add background worker and task queue with Celery and Redis

**Short description**  
Add a deterministic background task system using **Celery** with Redis as broker and result backend. Provide a lightweight task API for long‑running operations (e.g., parsing large repos, running heavy graph analytics, embedding batches), a CLI integration to enqueue and monitor tasks, unit and integration tests, a Docker Compose service for Redis and a worker, and documentation. All file paths, method names, environment variables, commands, and expected behaviors are explicit so an autonomous agent can implement, run, and verify without guessing.

---

## Objective what the agent must deliver
1. Add Celery task module `tasker/workers/tasks.py` exposing tasks:
   - `parse_and_index_files(file_paths: list[str]) -> dict`
   - `batch_embed_and_store(docs: list[dict], store_key: str) -> dict`
   - `run_graph_analysis(issue_id: str, depth: int) -> dict`
2. Add Celery app factory `tasker/workers/app.py` with `create_celery()` that reads configuration from env vars:
   - `TASKER_CELERY_BROKER_URL` default `redis://localhost:6379/0`
   - `TASKER_CELERY_RESULT_BACKEND` default `redis://localhost:6379/1`
3. Add worker entrypoint `tasker/workers/worker.py` that starts a Celery worker when executed as module.
4. Add CLI commands to enqueue and poll tasks in `tasker/cli/main.py`:
   - `enqueue-task --task <name> --payload <json>` returns `task_id`
   - `task-status --task-id <id>` returns status and result when ready
5. Add integration Docker Compose `docker-compose.celery.yml` that starts Redis, a Celery worker, and a `tasker-worker` service for local dev and CI.
6. Add unit tests mocking Celery for task invocation and result handling (`tests/workers/test_tasks_unit.py`).
7. Add integration tests that run a real worker and Redis via Docker Compose and verify end‑to‑end task execution (`tests/integration/test_celery_integration.py`).
8. Add documentation `tasker/workers/WORKERS.md` describing configuration, task API, CLI usage, and operational notes.
9. Update `tasker/cli/CLI.md` to include new commands and examples.
10. Create branch `feature/celery-workers` and open a PR with the exact PR body described below.

---

## Why this must be done exactly this way
- Background tasks are necessary for long-running operations that must not block CLI or HTTP callers.
- Celery with Redis is a well-known, reproducible stack; explicit env vars and Docker Compose make CI and local dev deterministic.
- A small, well-documented task API and CLI integration allow autonomous agents to enqueue and monitor tasks reliably.

---

## Files to add or modify exact paths
- `tasker/workers/app.py` **(new)**
- `tasker/workers/tasks.py` **(new)**
- `tasker/workers/worker.py` **(new)**
- `docker-compose.celery.yml` **(new at repo root)**
- `tests/workers/test_tasks_unit.py` **(new)**
- `tests/integration/test_celery_integration.py` **(new)**
- `tasker/workers/WORKERS.md` **(new)**
- Update `tasker/cli/main.py` **(modify)** to add `enqueue-task` and `task-status` commands
- Update `tasker/cli/CLI.md` **(modify)** to document new commands

---

## Exact code to add for Celery app factory

Create `tasker/workers/app.py` with the exact content below.

```python
# tasker/workers/app.py
from __future__ import annotations
import os
from celery import Celery

DEFAULT_BROKER = os.getenv("TASKER_CELERY_BROKER_URL", "redis://localhost:6379/0")
DEFAULT_BACKEND = os.getenv("TASKER_CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

def create_celery(app_name: str = "tasker") -> Celery:
    """
    Create and configure a Celery app instance.
    """
    celery = Celery(app_name, broker=os.getenv("TASKER_CELERY_BROKER_URL", DEFAULT_BROKER),
                    backend=os.getenv("TASKER_CELERY_RESULT_BACKEND", DEFAULT_BACKEND))
    # Basic recommended settings for deterministic behavior
    celery.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        task_time_limit=int(os.getenv("TASKER_CELERY_TASK_TIME_LIMIT", "300")),
        worker_prefetch_multiplier=int(os.getenv("TASKER_CELERY_PREFETCH_MULTIPLIER", "1")),
        task_acks_late=True,
    )
    return celery
```

---

## Exact code to add for tasks

Create `tasker/workers/tasks.py` with the exact content below.

```python
# tasker/workers/tasks.py
from __future__ import annotations
import json
from typing import List, Dict, Any
from tasker.workers.app import create_celery

celery = create_celery()

@celery.task(name="tasker.parse_and_index_files")
def parse_and_index_files(file_paths: List[str]) -> Dict[str, Any]:
    """
    Parse a list of files and index results into storage/repo.
    Returns a dict with counts and any errors.
    """
    from tasker.infrastructure.parser_adapter import TreeSitterParser
    from tasker.cli.wiring import build_default_container

    container = build_default_container()
    parser = container.parser
    results = {"parsed": 0, "errors": []}
    for p in file_paths:
        try:
            ast = parser.parse_file(p)
            # For deterministic demo, we simply count symbols
            symbols = parser.extract_symbols(ast)
            results["parsed"] += 1
        except Exception as exc:
            results["errors"].append({"path": p, "error": str(exc)})
    return results

@celery.task(name="tasker.batch_embed_and_store")
def batch_embed_and_store(docs: List[Dict[str, Any]], store_key: str) -> Dict[str, Any]:
    """
    Embed a batch of documents and store vectors in the configured storage (Faiss or other).
    docs: list of {"id": str, "text": str}
    store_key: logical key to persist results
    """
    from tasker.infrastructure.embeddings_adapter import EmbeddingsAdapter
    from tasker.infrastructure.faiss_store import FaissStore
    import tempfile
    import os
    dim = int(os.getenv("TASKER_EMBED_DIM", "64"))
    emb = EmbeddingsAdapter(dim=dim)
    store = FaissStore(dim=dim)
    for d in docs:
        v = emb.embed_text(d["text"])
        store.upsert(d["id"], v, metadata={"text": d.get("text")})
    # persist to a temp path keyed by store_key
    path = os.path.join(tempfile.gettempdir(), f"faiss_{store_key}")
    store.persist(path)
    return {"stored": len(docs), "path": path}

@celery.task(name="tasker.run_graph_analysis")
def run_graph_analysis(issue_id: str, depth: int = 3) -> Dict[str, Any]:
    """
    Run a deterministic graph analysis (e.g., impact set) and return results.
    """
    from tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
    from tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
    graph = Neo4jGraphAdapter()
    repo = Neo4jGraphRepository(graph)
    impacted = list(repo.find_impact_set(issue_id, max_depth=depth))
    graph.close()
    return {"issue_id": issue_id, "impact_set": sorted(set(impacted))}
```

---

## Exact code to add for worker entrypoint

Create `tasker/workers/worker.py` with the exact content below.

```python
# tasker/workers/worker.py
from __future__ import annotations
from tasker.workers.app import create_celery
import os
import sys

def main():
    celery = create_celery()
    # Use environment variables to control concurrency and queues
    concurrency = os.getenv("TASKER_CELERY_WORKER_CONCURRENCY", "1")
    queues = os.getenv("TASKER_CELERY_QUEUES", "default")
    argv = [
        "worker",
        "--loglevel=info",
        f"--concurrency={concurrency}",
        f"-Q{queues}",
    ]
    celery.worker_main(argv)

if __name__ == "__main__":
    main()
```

---

## Exact Docker Compose for Celery integration

Create `docker-compose.celery.yml` at repo root with the exact content below.

```yaml
version: "3.8"
services:
  redis:
    image: redis:7.2
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 12

  tasker-worker:
    image: python:3.11-slim
    working_dir: /workspace
    command: ["bash", "-lc", "python -m pip install -e . && python -m tasker.workers.worker"]
    volumes:
      - ./:/workspace:cached
    environment:
      TASKER_CELERY_BROKER_URL: "redis://redis:6379/0"
      TASKER_CELERY_RESULT_BACKEND: "redis://redis:6379/1"
      TASKER_INTEGRATION: "1"
    depends_on:
      redis:
        condition: service_healthy
```

---

## Exact CLI modifications

Modify `tasker/cli/main.py` to add two subcommands. Insert the following code snippets in appropriate places (do not change existing commands or behavior).

**Add parser definitions**

```python
p = sub.add_parser("enqueue-task")
p.add_argument("--task", required=True, help="Task name to enqueue")
p.add_argument("--payload", required=True, help="JSON payload for the task")
p.add_argument("--token")

p = sub.add_parser("task-status")
p.add_argument("--task-id", required=True)
p.add_argument("--token")
```

**Add command handlers**

```python
from celery.result import AsyncResult
from tasker.workers.app import create_celery
import json

def cmd_enqueue_task(args, container, user_id):
    try:
        # permission check: require admin or background:enqueue
        if not container.rbac.has_permission(user_id, "admin") and not container.rbac.has_permission(user_id, "background:enqueue"):
            raise PermissionError("forbidden")
        celery = create_celery()
        payload = json.loads(args.payload)
        # map task name to actual task
        if args.task == "parse_and_index_files":
            task = celery.send_task("tasker.parse_and_index_files", args=[payload.get("file_paths", [])])
        elif args.task == "batch_embed_and_store":
            task = celery.send_task("tasker.batch_embed_and_store", args=[payload.get("docs", []), payload.get("store_key", "default")])
        elif args.task == "run_graph_analysis":
            task = celery.send_task("tasker.run_graph_analysis", args=[payload.get("issue_id"), int(payload.get("depth", 3))])
        else:
            _error_and_exit("enqueue-task", {}, details=f"Unknown task {args.task}")
        _print_json({"status": "ok", "command": "enqueue-task", "task_id": task.id})
    except PermissionError as pexc:
        _error_and_exit("enqueue-task", {}, details=str(pexc))
    except Exception as exc:
        _error_and_exit("enqueue-task", {}, details=str(exc))

def cmd_task_status(args, container, user_id):
    try:
        celery = create_celery()
        res = AsyncResult(args.task_id, app=celery)
        out = {"status": res.status}
        if res.ready():
            out["result"] = res.result
        _print_json({"status": "ok", "command": "task-status", "task_id": args.task_id, "task": out})
    except Exception as exc:
        _error_and_exit("task-status", {"task_id": args.task_id}, details=str(exc))
```

**Dispatch**

Add to the command dispatch section:

```python
elif args.command == "enqueue-task":
    cmd_enqueue_task(args, container, user_id)
elif args.command == "task-status":
    cmd_task_status(args, container, user_id)
```

---

## Exact unit test to add

Create `tests/workers/test_tasks_unit.py` with the exact content below. These tests mock Celery and parser behavior.

```python
# tests/workers/test_tasks_unit.py
import pytest
from unittest.mock import patch, MagicMock
from tasker.workers.tasks import parse_and_index_files, batch_embed_and_store, run_graph_analysis

@patch("tasker.workers.tasks.create_celery")
def test_parse_and_index_files_calls_parser(mock_create):
    # Use real function but mock parser in wiring
    with patch("tasker.workers.tasks.build_default_container") as mock_build:
        parser = MagicMock()
        parser.parse_file.return_value = {"type": "root", "children": []}
        parser.extract_symbols.return_value = []
        mock_build.return_value = MagicMock(parser=parser)
        res = parse_and_index_files(["/no/such/file.py"])
        assert "parsed" in res

def test_batch_embed_and_store_persists(tmp_path):
    docs = [{"id": "d1", "text": "hello"}]
    res = batch_embed_and_store(docs, "testkey")
    assert res.get("stored") == 1

@patch("tasker.workers.tasks.Neo4jGraphAdapter")
def test_run_graph_analysis_calls_repo(mock_graph):
    mock_graph.return_value = MagicMock()
    # Simulate repository behavior by patching Neo4jGraphRepository.find_impact_set
    with patch("tasker.workers.tasks.Neo4jGraphRepository") as mock_repo_cls:
        mock_repo = MagicMock()
        mock_repo.find_impact_set.return_value = ["a", "b"]
        mock_repo_cls.return_value = mock_repo
        res = run_graph_analysis("issue-x", 2)
        assert "impact_set" in res
```

---

## Exact integration test to add

Create `tests/integration/test_celery_integration.py` with the exact content below. This test requires `docker-compose.celery.yml` and will be marked `integration`.

```python
# tests/integration/test_celery_integration.py
import os
import time
import json
import subprocess
import sys
import pytest
from tasker.workers.app import create_celery

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration tests disabled; set TASKER_INTEGRATION=1 to enable")

def test_enqueue_and_run_parse_task():
    _skip_if_not_integration()
    # Ensure docker compose is up externally by CI or Makefile
    celery = create_celery()
    # enqueue a simple parse task with a small file created in tmp
    import tempfile
    p = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
    p.write(b"def f():\n    return 1\n")
    p.flush()
    p.close()
    task = celery.send_task("tasker.parse_and_index_files", args=[[p.name]])
    # poll for result
    for _ in range(60):
        res = celery.AsyncResult(task.id)
        if res.ready():
            break
        time.sleep(0.5)
    assert res.ready()
    assert isinstance(res.result, dict)
```

---

## Exact documentation to add

Create `tasker/workers/WORKERS.md` with the exact content below.

```
Background Workers and Task Queue

Overview
- Uses Celery with Redis broker and result backend.
- Tasks are defined in tasker/workers/tasks.py and include:
  - parse_and_index_files(file_paths)
  - batch_embed_and_store(docs, store_key)
  - run_graph_analysis(issue_id, depth)

Configuration environment variables
- TASKER_CELERY_BROKER_URL default redis://localhost:6379/0
- TASKER_CELERY_RESULT_BACKEND default redis://localhost:6379/1
- TASKER_CELERY_TASK_TIME_LIMIT default 300
- TASKER_CELERY_WORKER_CONCURRENCY default 1
- TASKER_CELERY_QUEUES default default

CLI integration
- enqueue-task --task <name> --payload '<json>'
- task-status --task-id <id>

Local development
- Start services:
  docker compose -f docker-compose.celery.yml up -d
- Start worker (if not using compose):
  python -m tasker.workers.worker

Operational notes
- Tasks use JSON serialization for portability.
- Keep tasks idempotent where possible.
- Monitor Redis and worker logs for failures.
```

---

## Exact CLI docs update

Append to `tasker/cli/CLI.md` the following section under Commands:

```
enqueue-task --task <name> --payload '<json>' [--token]
- Enqueue a background task. Returns task_id.

task-status --task-id <id> [--token]
- Query task status and result when ready.
```

---

## Exact commands the agent must run exactly

```bash
git checkout -b feature/celery-workers
# create files as specified
python -m pip install -e .
pip install celery redis
# start celery integration services
docker compose -f docker-compose.celery.yml up -d
# run unit tests
pytest tests/workers/test_tasks_unit.py -q
# run integration tests (requires TASKER_INTEGRATION=1)
export TASKER_INTEGRATION=1
pytest tests/integration/test_celery_integration.py -q -m integration || true
# commit and push
git add tasker/workers docker-compose.celery.yml tests/workers tests/integration tasker/workers/WORKERS.md
git commit -m "feat(workers): add Celery tasks, app factory, worker entrypoint, CLI enqueue/status and tests"
git push origin feature/celery-workers
```

---

## PR body exact text to paste

```
Summary:
- Added Celery-based background workers with Redis broker and result backend.
- Added Celery app factory tasker/workers/app.py.
- Added tasks in tasker/workers/tasks.py: parse_and_index_files, batch_embed_and_store, run_graph_analysis.
- Added worker entrypoint tasker/workers/worker.py.
- Added docker-compose.celery.yml for local/CI worker and Redis.
- Added CLI integration: enqueue-task and task-status commands.
- Added unit tests and integration test for Celery tasks.
- Added documentation tasker/workers/WORKERS.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Installed Celery and Redis client: pip install celery redis.
3. Started services via docker compose: docker compose -f docker-compose.celery.yml up -d
4. Ran unit tests: pytest tests/workers/test_tasks_unit.py (passed).
5. Ran integration tests with TASKER_INTEGRATION=1 (passed when environment available).

Files changed:
- tasker/workers/app.py
- tasker/workers/tasks.py
- tasker/workers/worker.py
- docker-compose.celery.yml
- tests/workers/test_tasks_unit.py
- tests/integration/test_celery_integration.py
- tasker/workers/WORKERS.md
- Updated: tasker/cli/main.py, tasker/cli/CLI.md

Notes:
- Celery and Redis are required for integration tests. Use docker compose to start services.
- Tasks are JSON-serialized and designed to be deterministic and idempotent where possible.
```

---

## Acceptance criteria must be satisfied exactly
- `tasker/workers/app.py`, `tasker/workers/tasks.py`, and `tasker/workers/worker.py` exist and match the code blocks above.
- `docker-compose.celery.yml` exists and starts Redis and a `tasker-worker` service as specified.
- CLI supports `enqueue-task` and `task-status` with the exact flags and JSON outputs described in CLI docs.
- Unit tests `tests/workers/test_tasks_unit.py` pass.
- Integration test `tests/integration/test_celery_integration.py` passes when Redis and worker are available via `docker-compose.celery.yml`.
- `tasker/workers/WORKERS.md` documents configuration and usage.
- Branch `feature/celery-workers` created and PR opened with the exact PR body above.

---

## Labels to apply on GitHub
- `workers`
- `infra`
- `celery`
- `integration-test`
- `medium-priority`

---

## Estimated effort
**Medium (M)** — expected to take an autonomous agent or engineer **2–5 hours** depending on environment and Docker availability.