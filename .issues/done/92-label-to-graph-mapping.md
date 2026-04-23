# Issue #92: Label-to-Graph Mapping

## Description

Implement syncing GitHub Labels directly into Neo4j nodes for enhanced filtering. Labels in GitHub become nodes in Tasker's graph for richer querying.

## Requirements

- Fetch labels from GitHub repository on startup/sync
- Create Label nodes in Neo4j (or update existing)
- Link Issue nodes to Label nodes via HAS_LABEL relationship
- Support bi-directional sync (add label in GitHub -> appears in Tasker)
- Add filtering by labels in API and CLI: `GET /issues?labels=bug,urgent`
- Store label metadata: color, description, is_default

## Technical Details

### Neo4j Schema
```cypher
(:Issue)-[:HAS_LABEL]->(:Label {name: "bug", color: "d73a49"})
```

### API Endpoints
- `GET /labels` - List all labels (from GitHub and local)
- `GET /issues?labels=bug,urgent` - Filter issues by labels
- `POST /labels/sync` - Force sync from GitHub

### Sync Behavior
- On Tasker startup: fetch GitHub labels
- On webhook: update labels when changed in GitHub
- On issue creation: map GitHub labels to Label nodes

## Business Value

Leverages GitHub's labeling system within Tasker's graph for powerful filtering and analysis.

## Status: COMPLETED