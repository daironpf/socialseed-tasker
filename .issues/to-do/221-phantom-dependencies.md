# Issue #221: RAG-Powered "Phantom Dependency" Detection

## Description
Use semantic similarity (RAG) to identify issues that are conceptually related but lack explicit dependency links.

## Acceptance Criteria
- [ ] New CLI command `tasker analyze similarity --issue <id>`.
- [ ] API endpoint `/api/v1/analyze/similarity/{id}`.
- [ ] Logic to compare issue descriptions using vector embeddings.
- [ ] Suggest explicit dependencies if similarity score > threshold.

## Technical Notes
- Uses the RAG engine implementation from v0.9.0.
- Should suggest links to the user or agent.
