"""Real auto-healing pipeline executor (issue #520).

Runs a five-stage pipeline (test_failure -> neo4j_root_cause ->
task_generation -> agent_fix -> pr_created) against real backend resources:

- Stage 1 resolves the anchor issue in Neo4j (fails honestly when missing).
- Stage 2 runs :class:`RootCauseAnalyzer` over real closed issues.
- Stage 3 persists a real fix issue via :func:`create_issue_action`.
- Stage 4 applies a real code transformation to the workspace repository,
  stores the resulting unified diff as a ``.patch`` artifact and keeps a
  pre-fix backup so stages can be re-run.
- Stage 5 commits on a dedicated git branch when git is available
  (otherwise records a content snapshot hash).

Runs are persisted as JSON so they survive API restarts; leftover running
runs are marked as interrupted on boot. Stages execute sequentially on the
event loop with a configurable inter-stage delay so the UI can show live
progress and cancel mid-flight.
"""

from __future__ import annotations

import asyncio
import contextlib
import difflib
import hashlib
import os
import re
import shutil
import subprocess
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from socialseed_tasker.application.actions import create_issue_action
from socialseed_tasker.application.analyzer import RootCauseAnalyzer, TestFailure
from socialseed_tasker.healing.storage import HealingStorage

STAGE_ORDER: list[str] = [
    "test_failure",
    "neo4j_root_cause",
    "task_generation",
    "agent_fix",
    "pr_created",
]

STAGE_LABELS: dict[str, str] = {
    "test_failure": "Test Failure Detected",
    "neo4j_root_cause": "Neo4j Root Cause Analysis",
    "task_generation": "Task Generation",
    "agent_fix": "Agent Fix Attempt",
    "pr_created": "PR Created",
}

DEFAULT_HEALING_DIR = os.path.join(".tasker-data", "auto-healing")
_MAX_SCAN_BYTES = 200_000
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

# Workspace fixture: realistic files with auto-fixable defects (debug
# statements, trailing whitespace, missing final newline).
SEED_FILES: dict[str, str] = {
    "src/report.py": (
        '"""Weekly metrics report generator."""\n'
        "from __future__ import annotations\n"
        "\n"
        "from datetime import date\n"
        "\n"
        "\n"
        "def build_report(rows: list[dict]) -> str:\n"
        '    print("DEBUG: build_report started")\n'
        '    lines = [f"Report for {date.today()}"]\n'
        "    for row in rows:\n"
        '        print("DEBUG: processing row")\n'
        '        lines.append(f"- {row[\'name\']}: {row[\'value\']}")   \n'
        '    print("DEBUG: build_report finished")\n'
        '    return "\\n".join(lines)\n'
    ),
    "web/dashboard.js": (
        "// Dashboard summary widget\n"
        "export function renderSummary(stats) {\n"
        "  console.log('DEBUG: renderSummary', stats);\n"
        "  const total = stats.reduce((sum, s) => sum + s.count, 0);\n"
        "  console.log('DEBUG: total computed');\n"
        "  return { total, updatedAt: Date.now() };\n"
        "}\n"
    ),
    "notes/README.md": (
        "# Ops notes\n"
        "\n"
        "Weekly review checklist:\n"
        "- verify backups\n"
        "- rotate credentials"
    ),
}

_Strategy = dict[str, Any]

_STRATEGIES: list[_Strategy] = [
    {
        "name": "remove_debug_statements",
        "keywords": {"debug", "print", "log", "console", "statement", "leftover"},
        "description": "Removed leftover DEBUG print/console statements",
        "patterns": [
            re.compile(r"^\s*print\([^)]*[\"']DEBUG"),
            re.compile(r"^\s*console\.log\([^)]*[\"']DEBUG"),
        ],
    },
    {
        "name": "strip_trailing_whitespace",
        "keywords": {"whitespace", "trailing", "lint", "format", "spaces", "tabs"},
        "description": "Stripped trailing whitespace from source lines",
        "patterns": [],
    },
    {
        "name": "ensure_trailing_newline",
        "keywords": {"newline", "newlines", "eof", "eol", "ending"},
        "description": "Added missing newline at end of file",
        "patterns": [],
    },
]


class StageError(RuntimeError):
    """Recoverable stage failure: recorded on the stage, run marked failed."""


class RunNotFoundError(KeyError):
    """Raised when a run id does not exist."""


class RunConflictError(RuntimeError):
    """Raised when an operation conflicts with the current run state."""


class IssueLookupError(LookupError):
    """Raised at run creation when the anchor issue does not exist."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _duration_ms(started_at: str | None, completed_at: str | None) -> int | None:
    if not started_at or not completed_at:
        return None
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(completed_at)
    except ValueError:
        return None
    return max(0, int((end - start).total_seconds() * 1000))


class AutoHealingEngine:
    """Executes and persists auto-healing pipeline runs."""

    def __init__(
        self,
        storage: HealingStorage,
        repo_provider: Callable[[], Any],
        workspace: str | os.PathLike[str] | None = None,
        stage_delay: float | None = None,
        stage_timeout: float | None = None,
    ) -> None:
        self.storage = storage
        self._repo_provider = repo_provider
        env_dir = os.getenv("TASKER_HEALING_DIR") or DEFAULT_HEALING_DIR
        env_workspace = os.getenv("TASKER_HEALING_REPO")
        self.workspace = Path(workspace or env_workspace or (Path(env_dir) / "workspace"))
        if stage_delay is None:
            stage_delay = float(os.getenv("TASKER_HEALING_STAGE_DELAY", "1.0"))
        if stage_timeout is None:
            stage_timeout = float(os.getenv("TASKER_HEALING_STAGE_TIMEOUT", "60.0"))
        self.stage_delay = max(0.0, stage_delay)
        self.stage_timeout = max(1.0, stage_timeout)
        self._runs: dict[str, dict[str, Any]] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        for run in storage.load_runs():
            self._runs[run["id"]] = run
        self._mark_interrupted()
        self.ensure_workspace()

    # ------------------------------------------------------------- queries

    def list_runs(self) -> list[dict[str, Any]]:
        return sorted(self._runs.values(), key=lambda r: r.get("started_at") or "", reverse=True)

    def get_run(self, run_id: str) -> dict[str, Any]:
        run = self._runs.get(run_id)
        if run is None:
            raise RunNotFoundError(run_id)
        return run

    def list_patches(self, run_id: str) -> list[dict[str, Any]]:
        return list(self.get_run(run_id).get("patches") or [])

    def read_patch(self, run_id: str, patch_id: str) -> tuple[str, str] | None:
        for meta in self.list_patches(run_id):
            if meta["id"] == patch_id:
                content = self.storage.read_patch(run_id, patch_id)
                if content is None:
                    return None
                return content, meta.get("filename") or f"{patch_id}.patch"
        return None

    # ------------------------------------------------------------- control

    async def create_run(self, issue_id: str) -> dict[str, Any]:
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        issue = self._find_issue(issue_id)
        if issue is None:
            raise IssueLookupError(issue_id)
        repo = self._repo_provider()
        base_sha: str | None = None
        if self._git_available() and self._is_git_repo():
            base_sha = self._git("rev-parse", "HEAD") or None
        elif self._git_available():
            self._seed_git()
            base_sha = self._git("rev-parse", "HEAD") or None
        run: dict[str, Any] = {
            "id": run_id,
            "issue_id": str(issue_id),
            "issue_title": getattr(issue, "title", str(issue_id)),
            "repo": self.workspace.name,
            "branch": f"autohealing/{run_id}",
            "commit_sha": "",
            "stages": [
                {"id": sid, "label": STAGE_LABELS[sid], "status": "pending"} for sid in STAGE_ORDER
            ],
            "current_stage_index": 0,
            "started_at": _now(),
            "completed_at": None,
            "status": "running",
            "pr_url": None,
            "neo4j_node_id": None,
            "created_issue_id": None,
            "base_sha": base_sha,
            "patches": [],
            "logs": [],
        }
        if repo is None:
            self._log(run, "system", "[Auto-Healing] Warning: task repository unavailable")
        self._runs[run_id] = run
        self._log(run, "system", f"[Auto-Healing] Run created for issue {run['issue_id']}")
        self._save()
        self._spawn(run_id, 0)
        return run

    def cancel(self, run_id: str) -> dict[str, Any]:
        run = self.get_run(run_id)
        if run["status"] != "running":
            raise RunConflictError(f"run {run_id} is not running")
        run["status"] = "cancelled"
        run["completed_at"] = None
        for stage in run["stages"]:
            if stage["status"] == "running":
                stage["status"] = "cancelled"
                stage["details"] = "Cancelled by operator"
                stage["completed_at"] = _now()
        self._log(run, "system", "[Auto-Healing] Run cancelled by operator")
        self._save()
        task = self._tasks.get(run_id)
        if task is not None:
            task.cancel()
        return run

    async def restart(self, run_id: str, stage_id: str | None = None) -> dict[str, Any]:
        run = self.get_run(run_id)
        if run["status"] == "running":
            raise RunConflictError(f"run {run_id} is already running")
        if stage_id is not None and stage_id not in STAGE_ORDER:
            raise RunConflictError(f"unknown stage {stage_id}")
        index = self._restart_index(run, stage_id)
        fix_index = STAGE_ORDER.index("agent_fix")
        if index <= fix_index:
            self._revert_fix(run)
        for stage in run["stages"][index:]:
            stage_id = stage.get("id")
            stage.clear()
            stage.update({"id": stage_id, "label": STAGE_LABELS[stage_id], "status": "pending"})
        run["current_stage_index"] = index
        run["status"] = "running"
        run["completed_at"] = None
        self._log(run, "system", f"[Auto-Healing] Restarted from stage '{STAGE_ORDER[index]}'")
        self._save()
        self._spawn(run_id, index)
        return run

    def wait_for_task(self, run_id: str) -> asyncio.Task[None] | None:
        return self._tasks.get(run_id)

    # ------------------------------------------------------------ execution

    def _restart_index(self, run: dict[str, Any], stage_id: str | None) -> int:
        if stage_id is not None:
            return STAGE_ORDER.index(stage_id)
        for idx, stage in enumerate(run["stages"]):
            if stage.get("status") != "completed":
                return idx
        return 0

    def _revert_fix(self, run: dict[str, Any]) -> None:
        restored = self.storage.restore_backup(run["id"], self.workspace)
        if restored:
            self._log(run, "system", f"[Auto-Healing] Restored {len(restored)} file(s) to pre-fix state")
        for meta in list(run.get("patches") or []):
            if meta.get("stage_id") == "agent_fix":
                self.storage.delete_patch(run["id"], meta["id"])
        run["patches"] = [m for m in run.get("patches") or [] if m.get("stage_id") != "agent_fix"]
        run["commit_sha"] = ""
        if run.get("base_sha") and self._git_available() and self._is_git_repo():
            with contextlib.suppress(StageError):
                self._git("checkout", "--quiet", "-B", run["branch"], run["base_sha"])

    def _spawn(self, run_id: str, from_index: int) -> None:
        existing = self._tasks.get(run_id)
        if existing is not None and not existing.done():
            # Only reachable when a stale task outlived a cancel/restart.
            existing.cancel()
        task = asyncio.create_task(self._execute(run_id, from_index))
        self._tasks[run_id] = task

        def _cleanup(t: asyncio.Task[None], rid: str = run_id) -> None:
            if self._tasks.get(rid) is t:
                self._tasks.pop(rid, None)

        task.add_done_callback(_cleanup)

    async def _execute(self, run_id: str, from_index: int) -> None:
        for index in range(from_index, len(STAGE_ORDER)):
            run = self._runs.get(run_id)
            if run is None or run["status"] != "running":
                return
            stage = run["stages"][index]
            stage["status"] = "running"
            stage["started_at"] = _now()
            run["current_stage_index"] = index
            self._log(run, "system", f"[Auto-Healing] Stage '{stage['id']}' started")
            self._save()
            try:
                await asyncio.wait_for(self._run_stage(run, stage), timeout=self.stage_timeout)
            except asyncio.CancelledError:
                self._finish_stage_as_cancelled(run, stage)
                return
            except StageError as exc:
                self._fail_stage(run, stage, str(exc))
                return
            except Exception as exc:  # noqa: BLE001 - fail the run honestly
                self._fail_stage(run, stage, f"Internal error: {exc}")
                return
            stage["status"] = "completed"
            stage["completed_at"] = _now()
            stage["duration_ms"] = _duration_ms(stage.get("started_at"), stage.get("completed_at"))
            self._log(run, "system", f"[Auto-Healing] Stage '{stage['id']}' completed")
            self._save()
            if self.stage_delay > 0:
                try:
                    await asyncio.sleep(self.stage_delay)
                except asyncio.CancelledError:
                    self._finish_stage_as_cancelled(run, stage)
                    return
        run = self._runs.get(run_id)
        if run is not None and run["status"] == "running":
            run["status"] = "completed"
            run["completed_at"] = _now()
            self._log(run, "system", "[Auto-Healing] Pipeline completed successfully")
            self._save()

    def _finish_stage_as_cancelled(self, run: dict[str, Any], stage: dict[str, Any]) -> None:
        if stage.get("status") == "running":
            stage["status"] = "cancelled"
            stage["details"] = "Cancelled by operator"
            stage["completed_at"] = _now()
        if run.get("status") == "running":
            run["status"] = "cancelled"
        self._save()

    def _fail_stage(self, run: dict[str, Any], stage: dict[str, Any], message: str) -> None:
        stage["status"] = "failed"
        stage["completed_at"] = _now()
        stage["details"] = message[:240]
        run["status"] = "failed"
        run["completed_at"] = _now()
        self._log(run, "system", f"[Auto-Healing] Stage '{stage['id']}' failed: {message[:160]}")
        self._save()

    async def _run_stage(self, run: dict[str, Any], stage: dict[str, Any]) -> None:
        handlers: dict[str, Callable[..., Any]] = {
            "test_failure": self._stage_test_failure,
            "neo4j_root_cause": self._stage_root_cause,
            "task_generation": self._stage_task_generation,
            "agent_fix": self._stage_agent_fix,
            "pr_created": self._stage_pr_created,
        }
        await handlers[stage["id"]](run, stage)

    # ------------------------------------------------------------ stages

    async def _stage_test_failure(self, run: dict[str, Any], stage: dict[str, Any]) -> None:
        issue = self._find_issue(run["issue_id"])
        if issue is None:
            raise StageError(f"Issue {run['issue_id']} not found in Neo4j")
        run["issue_title"] = getattr(issue, "title", run["issue_title"])
        labels = ", ".join(getattr(issue, "labels", [])[:5]) or "none"
        stage["details"] = f"Failure linked to: {run['issue_title'][:60]}"
        self._log(run, "test", f"FAIL tracked issue: {run['issue_title']}")
        self._log(run, "system", f"[Auto-Healing] Issue {run['issue_id'][:8]} labels: {labels}")

    async def _stage_root_cause(self, run: dict[str, Any], stage: dict[str, Any]) -> None:
        repo = self._require_repo()
        issue = self._find_issue(run["issue_id"])
        if issue is None:
            raise StageError(f"Issue {run['issue_id']} not found in Neo4j")
        component_name = "unknown"
        try:
            component = repo.get_component(getattr(issue, "component_id", None))
            if component is not None:
                component_name = component.name
        except Exception:
            pass
        failure = TestFailure(
            test_id=run["id"],
            test_name=run["issue_title"],
            error_message=(getattr(issue, "description", "") or "auto-healing run")[:400],
            stack_trace="",
            component=component_name,
            labels=list(getattr(issue, "labels", []) or []),
        )
        closed_issues = [
            candidate
            for candidate in repo.list_issues()
            if str(getattr(getattr(candidate, "status", None), "value", "")) == "CLOSED"
        ]
        links = RootCauseAnalyzer(repo).find_root_cause(failure, closed_issues)
        if links:
            top = links[0]
            stage["details"] = f"{top.confidence:.2f} - {top.issue.title[:48]}"
            self._log(run, "system", f"[Neo4j] Found {len(links)} candidate root cause(s)")
            for reason in top.reasons[:3]:
                self._log(run, "system", f"[Neo4j] {reason}")
        else:
            stage["details"] = "No historical root cause found"
            self._log(run, "system", "[Neo4j] No closed issues available for correlation")

    async def _stage_task_generation(self, run: dict[str, Any], stage: dict[str, Any]) -> None:
        repo = self._require_repo()
        title = f"[Auto-Healing] Fix: {run['issue_title']}"[:200]
        description = (
            f"Automated fix task generated by pipeline `{run['id']}`.\n\n"
            f"- Source issue: `{run['issue_id']}`\n"
            f"- Run: `{run['id']}` in the Auto-Healing monitor"
        )
        try:
            created, warnings = create_issue_action(
                repo,
                title=title,
                description=description,
                priority="HIGH",
                labels=["auto-healing", "pipeline", run["id"]],
            )
        except Exception as exc:
            raise StageError(f"Could not create fix issue: {exc}") from exc
        run["created_issue_id"] = str(created.id)
        stage["details"] = f"Created issue {str(created.id)[:8]}"
        self._log(run, "system", f"[Tasker] Created fix issue {str(created.id)[:8]}: {title[:60]}")
        for warning in warnings[:2]:
            self._log(run, "system", f"[Tasker] {warning}")

    async def _stage_agent_fix(self, run: dict[str, Any], stage: dict[str, Any]) -> None:
        context_text = " ".join(
            [run["issue_title"], run["issue_id"]] + list(self._context_labels(run))
        )
        selected = self._select_strategy(context_text)
        order = [selected] + [s["name"] for s in _STRATEGIES if s["name"] != selected] if selected else [
            s["name"] for s in _STRATEGIES
        ]
        matches: list[tuple[str, str, str]] = []
        chosen: dict[str, Any] | None = None
        for name in order:
            strategy = next(s for s in _STRATEGIES if s["name"] == name)
            matches = self._collect_matches(strategy)
            if matches:
                chosen = strategy
                break
        if chosen is None or not matches:
            names = ", ".join(s["name"] for s in _STRATEGIES)
            raise StageError(f"No auto-fixable pattern found in {self.workspace.name} (tried: {names})")
        backups = {rel: original for rel, original, _ in matches}
        self.storage.save_backup(run["id"], backups)
        for rel, _, new_content in matches:
            target = self.workspace / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(new_content, encoding="utf-8")
        diff = self._build_diff(matches)
        if not diff.strip():
            raise StageError("Fix produced an empty diff")
        patch_id = f"patch-{uuid.uuid4().hex[:8]}"
        self.storage.save_patch(run["id"], patch_id, diff)
        first_file = matches[0][0]
        meta = {
            "id": patch_id,
            "run_id": run["id"],
            "stage_id": "agent_fix",
            "strategy": chosen["name"],
            "filename": f"{Path(first_file).stem}_{patch_id}.patch",
            "files": [rel for rel, _, _ in matches],
            "created_at": _now(),
            "size_bytes": len(diff.encode("utf-8")),
            "commit_sha": "",
        }
        run.setdefault("patches", []).append(meta)
        run["last_diff"] = diff
        stage["details"] = chosen["description"]
        self._log(run, "agent", f"[Agent] Applied strategy {chosen['name']} to {len(matches)} file(s)")
        for rel, _, _ in matches:
            self._log(run, "agent", f"[Agent] Changed {rel}")

    async def _stage_pr_created(self, run: dict[str, Any], stage: dict[str, Any]) -> None:
        sha = ""
        if run.get("base_sha") and self._git_available() and self._is_git_repo():
            sha = self._git_commit(run)
        if not sha:
            diff = run.get("last_diff") or ""
            sha = hashlib.sha1((diff or run["id"]).encode("utf-8")).hexdigest()[:12]
            stage["details"] = f"Snapshot {sha} (git unavailable)"
            self._log(run, "system", f"[Auto-Healing] Workspace snapshot {sha} (no git)")
        else:
            run["commit_sha"] = sha
            stage["details"] = f"{run['branch']} @ {sha}"
            self._log(run, "system", f"[Git] Committed on {run['branch']} ({sha})")
        if sha and not run.get("commit_sha"):
            run["commit_sha"] = sha
        for meta in run.get("patches") or []:
            meta["commit_sha"] = run["commit_sha"] or sha

    # ----------------------------------------------------------- strategies

    def _context_labels(self, run: dict[str, Any]) -> list[str]:
        issue = self._find_issue(run["issue_id"])
        return list(getattr(issue, "labels", []) or [])

    def _select_strategy(self, text: str) -> str | None:
        tokens = set(re.findall(r"[a-z]+", text.lower()))
        for strategy in _STRATEGIES:
            if tokens & strategy["keywords"]:
                return str(strategy["name"])
        return None

    def _iter_workspace_files(self) -> list[Path]:
        files: list[Path] = []
        if not self.workspace.exists():
            return files
        for path in sorted(self.workspace.rglob("*")):
            if not path.is_file():
                continue
            rel_parts = path.relative_to(self.workspace).parts
            if any(part in _SKIP_DIRS for part in rel_parts):
                continue
            try:
                if path.stat().st_size > _MAX_SCAN_BYTES:
                    continue
            except OSError:
                continue
            files.append(path)
        return files

    def _collect_matches(self, strategy: dict[str, Any]) -> list[tuple[str, str, str]]:
        matches: list[tuple[str, str, str]] = []
        for path in self._iter_workspace_files():
            try:
                original = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            updated = self._transform(original, strategy)
            if updated != original:
                rel = str(path.relative_to(self.workspace)).replace(os.sep, "/")
                matches.append((rel, original, updated))
        return matches

    @staticmethod
    def _transform(content: str, strategy: dict[str, Any]) -> str:
        name = strategy["name"]
        if name == "remove_debug_statements":
            kept = [
                line
                for line in content.splitlines(keepends=True)
                if not any(pattern.search(line) for pattern in strategy["patterns"])
            ]
            return "".join(kept)
        if name == "strip_trailing_whitespace":
            lines = content.splitlines(keepends=True)
            stripped = []
            for line in lines:
                body = line.rstrip("\r\n")
                ending = line[len(body) :]
                stripped.append(body.rstrip(" \t") + ending)
            return "".join(stripped)
        if name == "ensure_trailing_newline":
            if content and not content.endswith("\n"):
                return content + "\n"
            return content
        return content

    @staticmethod
    def _build_diff(matches: list[tuple[str, str, str]]) -> str:
        chunks: list[str] = []
        for rel, original, updated in matches:
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
            )
            chunks.append("".join(diff))
        return "\n".join(chunks)

    # ------------------------------------------------------------- git

    def _git_available(self) -> bool:
        return shutil.which("git") is not None

    def _is_git_repo(self) -> bool:
        return (self.workspace / ".git").exists()

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.workspace), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        if result.returncode != 0:
            raise StageError(f"git {' '.join(args[:2])} failed: {result.stderr.strip()[:180]}")
        return result.stdout.strip()

    def _seed_git(self) -> None:
        try:
            if not self._is_git_repo():
                self._git("init", "--quiet")
                self._git("add", "-A")
                self._git(
                    "-c",
                    "user.email=autohealing@local",
                    "-c",
                    "user.name=auto-healing",
                    "commit",
                    "--quiet",
                    "-m",
                    "seed workspace",
                )
        except StageError:
            return

    def _git_commit(self, run: dict[str, Any]) -> str:
        status = self._git("status", "--porcelain")
        on_branch = self._git("rev-parse", "--abbrev-ref", "HEAD")
        if on_branch != run["branch"]:
            if self._branch_exists(run["branch"]):
                self._git("checkout", "--quiet", run["branch"])
            elif status:
                self._git("checkout", "--quiet", "-b", run["branch"])
        if status:
            self._git("add", "-A")
            self._git(
                "-c",
                "user.email=autohealing@local",
                "-c",
                "user.name=auto-healing",
                "commit",
                "--quiet",
                "-m",
                f"auto-healing: {run['issue_title'][:80]}",
            )
        return self._git("rev-parse", "--short", "HEAD")

    def _branch_exists(self, branch: str) -> bool:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.workspace), "rev-parse", "--verify", "--quiet", branch],
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0

    # ------------------------------------------------------------ helpers

    def _require_repo(self) -> Any:
        repo = self._repo_provider()
        if repo is None:
            raise StageError("Task repository unavailable")
        return repo

    def _find_issue(self, issue_id: str) -> Any | None:
        repo = self._repo_provider()
        if repo is None:
            return None
        try:
            return repo.get_issue(str(issue_id))
        except Exception:
            return None

    def ensure_workspace(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)
        for rel, content in SEED_FILES.items():
            path = self.workspace / rel
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
        if self._git_available() and not self._is_git_repo():
            self._seed_git()

    def _mark_interrupted(self) -> None:
        changed = False
        for run in self._runs.values():
            if run.get("status") == "running":
                run["status"] = "failed"
                run["completed_at"] = _now()
                for stage in run["stages"]:
                    if stage.get("status") == "running":
                        stage["status"] = "failed"
                        stage["details"] = "Interrupted by API restart"
                        stage["completed_at"] = _now()
                changed = True
        if changed:
            self._save()

    def _log(self, run: dict[str, Any], source: str, content: str) -> None:
        run.setdefault("logs", []).append(
            {
                "id": str(uuid.uuid4()),
                "run_id": run["id"],
                "timestamp": _now(),
                "source": source,
                "content": content,
            }
        )

    def _save(self) -> None:
        self.storage.save_runs(list(self._runs.values()))
