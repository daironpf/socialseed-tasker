"""Idempotent import of the bundled workflow definitions (issue #575).

Parses the ``.md`` files of ``.agent/workflows`` (repo checkout, when present)
and the packaged templates in ``assets/templates/workflows`` (always shipped
inside the Docker image) into ``source='builtin'`` rows. ``slug`` = file stem,
``name`` = first ``# `` heading (``Workflow: `` prefix stripped) and
``description`` = first prose paragraph. Existing rows are never overwritten
(``ON CONFLICT (slug) DO NOTHING``), so user edits and prior imports survive.

Enable/disable with ``TASKER_WORKFLOWS_SEED`` (default ``true``); point
``TASKER_WORKFLOWS_DIR`` at a custom directory to override the repo folder.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "templates" / "workflows"
_WORKFLOW_HEADING = "# "


def parse_workflow_markdown(slug: str, text: str) -> dict[str, Any]:
    """Extract ``slug``/``name``/``description``/``content_md`` from one file."""
    lines = text.splitlines()
    name = slug.replace("-", " ").title()
    description: str | None = None
    in_front_matter = False
    for index, raw in enumerate(lines):
        line = raw.strip()
        if index == 0 and line == "---":
            in_front_matter = True
            continue
        if in_front_matter:
            if line == "---":
                in_front_matter = False
            continue
        if line.startswith(_WORKFLOW_HEADING):
            heading = line[len(_WORKFLOW_HEADING) :].strip()
            if heading.lower().startswith("workflow:"):
                heading = heading.split(":", 1)[1].strip()
            if heading:
                name = heading
            continue
        if description is None and line and not line.startswith("#"):
            description = line.replace("**", "").replace("`", "").strip().strip("_").strip()
            if len(description) > 280:
                description = description[:277] + "..."
    return {"slug": slug, "name": name, "description": description, "content_md": text}


def _collect_dir(directory: Path, collected: dict[str, dict[str, Any]]) -> None:
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("*.md")):
        slug = path.stem
        if slug.lower() == "readme" or slug in collected:
            continue
        try:
            collected[slug] = parse_workflow_markdown(slug, path.read_text(encoding="utf-8"))
        except OSError as exc:
            logger.warning("workflow file skipped (%s): %s", path.name, exc)


def collect_builtin_workflows() -> list[dict[str, Any]]:
    """Collect the builtin definitions: repo ``.agent/workflows`` first, then assets."""
    collected: dict[str, dict[str, Any]] = {}
    repo_dir = Path(os.getenv("TASKER_WORKFLOWS_DIR") or (Path.cwd() / ".agent" / "workflows"))
    _collect_dir(repo_dir, collected)
    _collect_dir(_ASSETS_DIR, collected)
    return [collected[slug] for slug in sorted(collected)]


def seed_workflows(database_url: str | None) -> dict[str, int] | None:
    """Import builtin workflows; None when TASKER_DATABASE_URL is not configured."""
    if not database_url:
        return None
    from socialseed_tasker.auth.user_store import PostgresWorkflowStore

    entries = collect_builtin_workflows()
    inserted = PostgresWorkflowStore(database_url).seed_builtin(entries)
    return {"total": len(entries), "inserted": inserted}


def workflows_seed_enabled() -> bool:
    """TASKER_WORKFLOWS_SEED defaults to true (idempotent, safe on every boot)."""
    return os.getenv("TASKER_WORKFLOWS_SEED", "true").lower() != "false"
