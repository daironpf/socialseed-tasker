"""Cypher query definitions for Neo4j graph operations.

All queries are parameterized to prevent Cypher injection.
Organized by entity: components, issues, relationships.
"""

# ---------------------------------------------------------------------------
# Schema initialization
# ---------------------------------------------------------------------------

SCHEMA_CONSTRAINTS = [
    "CREATE CONSTRAINT issue_id IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
    "CREATE INDEX issue_status IF NOT EXISTS FOR (i:Issue) ON (i.status)",
    "CREATE INDEX issue_component IF NOT EXISTS FOR (i:Issue) ON (i.component_id)",
    "CREATE INDEX issue_priority IF NOT EXISTS FOR (i:Issue) ON (i.priority)",
    "CREATE INDEX issue_labels IF NOT EXISTS FOR (i:Issue) ON i.labels",
    "CREATE INDEX label_name IF NOT EXISTS FOR (l:Label) ON (l.name)",
]

# ---------------------------------------------------------------------------
# Component queries
# ---------------------------------------------------------------------------

CREATE_COMPONENT = """
CREATE (c:Component {
    id: $id,
    name: $name,
    description: $description,
    project: $project,
    created_at: $created_at,
    updated_at: $updated_at
})
"""

GET_COMPONENT = """
MATCH (c:Component {id: $id})
RETURN c
"""

LIST_COMPONENTS = """
MATCH (c:Component)
WHERE $project IS NULL OR c.project = $project
RETURN c
ORDER BY c.name
"""

UPDATE_COMPONENT = """
MATCH (c:Component {id: $id})
SET c += $updates
SET c.updated_at = $updated_at
RETURN c
"""

DELETE_COMPONENT = """
MATCH (c:Component {id: $id})
DETACH DELETE c
"""

# ---------------------------------------------------------------------------
# Issue queries
# ---------------------------------------------------------------------------

CREATE_ISSUE = """
MATCH (c:Component {id: $component_id})
CREATE (i:Issue {
    id: $id,
    title: $title,
    description: $description,
    status: $status,
    priority: $priority,
    component_id: $component_id,
    labels: $labels,
    dependencies: $dependencies,
    blocks: $blocks,
    affects: $affects,
    created_at: $created_at,
    updated_at: $updated_at,
    closed_at: $closed_at,
    architectural_constraints: $architectural_constraints,
    agent_working: $agent_working,
    agent_started_at: $agent_started_at,
    agent_finished_at: $agent_finished_at,
    agent_id: $agent_id,
    reasoning_logs: $reasoning_logs,
    manifest_todo: $manifest_todo,
    manifest_files: $manifest_files,
    manifest_notes: $manifest_notes
})
CREATE (i)-[:BELONGS_TO]->(c)
"""

GET_ISSUE = """
MATCH (i:Issue {id: $id})
RETURN i
"""

UPDATE_ISSUE = """
MATCH (i:Issue {id: $id})
SET i += $updates
SET i.updated_at = $updated_at
RETURN i
"""

CLOSE_ISSUE = """
MATCH (i:Issue {id: $id})
SET i.status = 'CLOSED', i.closed_at = $closed_at, i.updated_at = $updated_at
RETURN i
"""

DELETE_ISSUE = """
MATCH (i:Issue {id: $id})
DETACH DELETE i
"""

LIST_ISSUES = """
MATCH (i:Issue)
OPTIONAL MATCH (i)-[:BELONGS_TO]->(c:Component)
WHERE ($component_id IS NULL OR i.component_id = $component_id)
  AND (size($statuses) = 0 OR i.status IN $statuses)
  AND ($project IS NULL OR c.project = $project)
OPTIONAL MATCH (i)-[:DEPENDS_ON]->(dep:Issue)
OPTIONAL MATCH (i)<-[:DEPENDS_ON]-(blocked:Issue)
WITH i, collect(DISTINCT dep.id) AS dep_ids, collect(DISTINCT blocked.id) AS blocked_ids
RETURN i, dep_ids, blocked_ids
ORDER BY i.created_at DESC
"""

# ---------------------------------------------------------------------------
# Dependency queries
# ---------------------------------------------------------------------------

ADD_DEPENDENCY = """
MATCH (source:Issue {id: $issue_id})
MATCH (target:Issue {id: $depends_on_id})
MERGE (source)-[:DEPENDS_ON]->(target)
"""

REMOVE_DEPENDENCY = """
MATCH (source:Issue {id: $issue_id})-[r:DEPENDS_ON]->(target:Issue {id: $depends_on_id})
DELETE r
"""

GET_DEPENDENCIES = """
MATCH (source:Issue {id: $issue_id})-[:DEPENDS_ON]->(target:Issue)
RETURN target
ORDER BY target.created_at DESC
"""

GET_DEPENDENTS = """
MATCH (target:Issue {id: $issue_id})<-[:DEPENDS_ON]-(source:Issue)
RETURN source
ORDER BY source.created_at DESC
"""

GET_DEPENDENCY_CHAIN = """
MATCH path = (start:Issue {id: $issue_id})-[:DEPENDS_ON*1..]->(dep:Issue)
RETURN DISTINCT dep, length(path) AS distance
ORDER BY distance
"""

CHECK_CYCLE = """
MATCH (target:Issue {id: $depends_on_id})
OPTIONAL MATCH path = (target)-[:DEPENDS_ON*1..]->(source:Issue {id: $issue_id})
RETURN path IS NOT NULL AS would_cycle
"""

# ---------------------------------------------------------------------------
# Label queries
# ---------------------------------------------------------------------------

CREATE_LABEL = """
MERGE (l:Label {name: $name})
SET l.color = $color,
    l.description = $description,
    l.is_default = $is_default,
    l.updated_at = $updated_at
RETURN l
"""

GET_ALL_LABELS = """
MATCH (l:Label)
RETURN l ORDER BY l.name
"""

GET_ISSUE_LABELS = """
MATCH (i:Issue {id: $issue_id})-[r:HAS_LABEL]->(l:Label)
RETURN l
"""

LINK_ISSUE_TO_LABEL = """
MATCH (i:Issue {id: $issue_id})
MATCH (l:Label {name: $label_name})
MERGE (i)-[:HAS_LABEL]->(l)
"""

GET_ISSUES_BY_LABELS = """
MATCH (i:Issue)-[:HAS_LABEL]->(l:Label)
WHERE l.name IN $labels
WITH i, collect(DISTINCT l.name) AS issue_labels
WHERE size($labels) = size([x IN $labels WHERE x IN issue_labels])
RETURN i
"""

DELETE_LABEL = """
MATCH (l:Label {name: $name})
DETACH DELETE l
"""
