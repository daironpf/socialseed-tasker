"""Canonical application use cases — pure domain logic with dependency injection.

Both functions depend only on application ports and repository protocols,
never on infrastructure classes.  They accept GraphRepository, IssueRepository,
and ParserPort as explicit parameters for deterministic testing and wiring.
"""

from __future__ import annotations

from typing import Any

from socialseed_tasker.application.dtos import IssueDTO
from socialseed_tasker.application.exceptions import GraphPortError, ParserError
from socialseed_tasker.application.ports import ParserPort
from socialseed_tasker.application.repositories import GraphRepository, IssueRepository


def calculate_impact(
    issue_id: str,
    max_depth: int,
    graph_repo: GraphRepository,
) -> list[str]:
    """Deterministic impact calculation.

    Calls graph_repo.find_impact_set(issue_id, max_depth), deduplicates,
    and returns a sorted list of unique impacted issue ids.
    Raises GraphPortError on repository failures.
    """
    try:
        impacted = list(graph_repo.find_impact_set(issue_id, max_depth))
        unique = sorted(set(impacted))
        return unique
    except Exception as exc:
        raise GraphPortError(f"calculate_impact failed for {issue_id}: {exc}") from exc


def generate_agent_context(
    issue_id: str,
    max_depth: int,
    graph_repo: GraphRepository,
    issue_repo: IssueRepository,
    parser: ParserPort,
) -> dict[str, Any]:
    """Generate structured context for an agent.

    Output shape::

        {
          "issue": { ... } or None,
          "impact_set": ["issue-a", ...],
          "related_code": { "<id>": { "files": { "<path>": {"symbols": [...], "imports": [...]} } } },
          "reasoning": ["step 1", ...]
        }
    """
    reasoning: list[str] = []
    try:
        reasoning.append(f"Start context generation for issue {issue_id} with max_depth={max_depth}")

        issue = issue_repo.get(issue_id)
        reasoning.append(f"Loaded issue {issue_id}: {'found' if issue else 'missing'}")

        impact = calculate_impact(issue_id, max_depth, graph_repo)
        reasoning.append(f"Calculated impact set of size {len(impact)}")

        related_code: dict[str, Any] = {}
        all_ids = [issue_id] + [i for i in impact if i != issue_id]

        for iid in all_ids:
            try:
                reasoning.append(f"Fetching issue data for {iid}")
                iobj = issue_repo.get(iid)
                if iobj is None:
                    reasoning.append(f"Issue {iid} not found; skipping files")
                    continue

                files: list[str] = []
                try:
                    files = list(iobj.metadata.get("files", [])) if getattr(iobj, "metadata", None) else []
                except Exception:
                    files = []

                if not files:
                    reasoning.append(f"No files listed for {iid}")
                    continue

                related_code[iid] = {"files": {}}
                for path in files:
                    try:
                        reasoning.append(f"Parsing file {path} for issue {iid}")
                        ast = parser.parse_file(path)
                        symbols = parser.extract_symbols(ast)
                        imports = parser.extract_imports(ast)
                        related_code[iid]["files"][path] = {"symbols": symbols, "imports": imports}
                        reasoning.append(f"Parsed file {path}: symbols={len(symbols)}, imports={len(imports)}")
                    except ParserError as pexc:
                        reasoning.append(f"ParserError for {path}: {pexc}")
                    except Exception as exc:
                        reasoning.append(f"Unexpected parser error for {path}: {exc}")
            except Exception as exc:
                reasoning.append(f"Failed to fetch or process issue {iid}: {exc}")

        issue_dict = None
        if issue is not None:
            issue_dict = {
                "id": issue.id,
                "title": issue.title,
                "description": issue.description,
                "status": issue.status,
                "metadata": dict(issue.metadata or {}),
            }

        reasoning.append("Context generation completed")
        return {
            "issue": issue_dict,
            "impact_set": impact,
            "related_code": related_code,
            "reasoning": reasoning,
        }
    except Exception as exc:
        reasoning.append(f"generate_agent_context failed: {exc}")
        raise GraphPortError(f"generate_agent_context failed for {issue_id}: {exc}") from exc
