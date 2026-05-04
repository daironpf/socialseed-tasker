# Issue #224: Self-Healing Documentation System

## Description
Automated monitoring of documentation "rot" by comparing source code state with project documentation.

## Acceptance Criteria
- [x] Background task to compare `project.md` with actual project structure.
- [x] Detection of missing API endpoints in `API_REFERENCE.md`.
- [x] Automatic creation of `DOC_GAP` issues when discrepancies are found.

## Status: DONE

## Resolution (2026-05-04)
- [x] Add `tasker constraints doc-gaps` command
- [x] compares OpenAPI schema with docs/API_REFERENCE.md
- [x] Returns table of undocumented endpoints
- [x] Lists ~15 gaps per run

### Files Changed
- `commands.py`: Added doc-gaps command under constraints

### Usage
```bash
tasker constraints doc-gaps

# Output shows undocumented endpoints:
# Endpoint
# ---------------------------
# POST /api/v1/analyze/similarity/{issue_id}
# GET /api/v1/code-graph/issues/{file_path}
```
