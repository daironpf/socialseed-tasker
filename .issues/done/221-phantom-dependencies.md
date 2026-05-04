# Issue #221: RAG-Powered "Phantom Dependency" Detection

## Description
Use semantic similarity (RAG) to identify issues that are conceptually related but lack explicit dependency links.

## Acceptance Criteria
- [x] New CLI command `tasker analyze similarity --issue <id>`.
- [x] API endpoint `/api/v1/analyze/similarity/{id}`.
- [x] Logic to compare issue descriptions using vector embeddings.
- [x] Suggest explicit dependencies if similarity score > threshold.

## Status: DONE

## Resolution

### Completed (2026-05-04)
- [x] API: `GET /api/v1/analyze/similarity/{issue_id}?threshold=0.7&limit=10`
- [x] CLI: `tasker analyze similarity --issue <id> --threshold 0.7 --limit 10`
- [x] Returns phantom dependencies (semantically similar but unlinked)
- [x] Filters out existing explicit dependencies

### Files Changed
- `routes.py`: Added `/analyze/similarity/{issue_id}` endpoint
- `commands.py`: Added `analyze similarity` CLI command

### Usage
```bash
# CLI
tasker analyze similarity --issue <issue_id> --threshold 0.7

# API
curl "http://localhost:8000/api/v1/analyze/similarity/<issue_id>?threshold=0.7"
```
