"""Cypher query definitions for Neo4j graph operations.

All queries are parameterized to prevent Cypher injection.
Organized by entity: components, issues, relationships.

PERFORMANCE OPTIMIZATION:
- Schema constraints ensure unique IDs (primary key behavior)
- Indexes are created for frequently queried properties
- BFS traversal uses index lookups as starting points
"""

# ---------------------------------------------------------------------------
# Schema initialization
# ---------------------------------------------------------------------------

SCHEMA_CONSTRAINTS = [
    "CREATE CONSTRAINT issue_id IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT code_file_id IF NOT EXISTS FOR (f:CodeFile) REQUIRE f.id IS UNIQUE",
    "CREATE CONSTRAINT code_symbol_id IF NOT EXISTS FOR (s:CodeSymbol) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT code_import_id IF NOT EXISTS FOR (i:CodeImport) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT reasoning_id IF NOT EXISTS FOR (r:ReasoningNode) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
]

SCHEMA_INDEXES = [
    "CREATE INDEX issue_status IF NOT EXISTS FOR (i:Issue) ON (i.status)",
    "CREATE INDEX issue_component IF NOT EXISTS FOR (i:Issue) ON (i.component_id)",
    "CREATE INDEX issue_priority IF NOT EXISTS FOR (i:Issue) ON (i.priority)",
    "CREATE INDEX issue_labels IF NOT EXISTS FOR (i:Issue) ON i.labels",
    "CREATE INDEX issue_created_at IF NOT EXISTS FOR (i:Issue) ON (i.created_at)",
    "CREATE INDEX issue_project IF NOT EXISTS FOR (i:Issue) ON (i.project)",
    "CREATE INDEX component_name IF NOT EXISTS FOR (c:Component) ON (c.name)",
    "CREATE INDEX component_project IF NOT EXISTS FOR (c:Component) ON (c.project)",
    "CREATE INDEX label_name IF NOT EXISTS FOR (l:Label) ON (l.name)",
    "CREATE INDEX deployment_commit IF NOT EXISTS FOR (d:Deployment) ON (d.commit_sha)",
    "CREATE INDEX deployment_environment IF NOT EXISTS FOR (d:Deployment) ON (d.environment)",
    "CREATE INDEX code_file_path IF NOT EXISTS FOR (f:CodeFile) ON (f.path)",
    "CREATE INDEX code_file_name IF NOT EXISTS FOR (f:CodeFile) ON (f.name)",
    "CREATE INDEX code_file_repo IF NOT EXISTS FOR (f:CodeFile) ON (f.repository_path)",
    "CREATE INDEX code_symbol_name IF NOT EXISTS FOR (s:CodeSymbol) ON (s.name)",
    "CREATE INDEX code_symbol_type IF NOT EXISTS FOR (s:CodeSymbol) ON (s.symbol_type)",
    "CREATE INDEX code_symbol_file IF NOT EXISTS FOR (s:CodeSymbol) ON (s.file_id)",
    "CREATE INDEX code_import_file IF NOT EXISTS FOR (i:CodeImport) ON (i.file_id)",
    "CREATE INDEX reasoning_issue IF NOT EXISTS FOR (r:ReasoningNode) ON (r.issue_id)",
    "CREATE INDEX reasoning_type IF NOT EXISTS FOR (r:ReasoningNode) ON (r.decision_type)",
    "CREATE INDEX reasoning_created IF NOT EXISTS FOR (r:ReasoningNode) ON (r.created_at)",
    "CREATE INDEX agent_id_idx IF NOT EXISTS FOR (a:Agent) ON (a.id)",
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

LIST_PROJECTS = """
MATCH (c:Component)
RETURN DISTINCT c.project AS name
ORDER BY name
"""

LIST_ISSUES_PAGINATED = """
MATCH (i:Issue)
USING INDEX i:Issue(status)
WHERE ($component_id IS NULL OR i.component_id = $component_id)
  AND ($statuses IS NULL OR i.status IN $statuses)
  AND ($project IS NULL OR i.project = $project)
RETURN i
ORDER BY i.created_at DESC
SKIP $skip
LIMIT $limit
"""

COUNT_ISSUES = """
MATCH (i:Issue)
WHERE ($component_id IS NULL OR i.component_id = $component_id)
  AND ($statuses IS NULL OR i.status IN $statuses)
  AND ($project IS NULL OR i.project = $project)
RETURN count(i) as total
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
# Component Dependency queries
# ---------------------------------------------------------------------------

ADD_COMPONENT_DEPENDENCY = """
MATCH (source:Component {id: $component_id})
MATCH (target:Component {id: $depends_on_id})
MERGE (source)-[:DEPENDS_ON]->(target)
"""

REMOVE_COMPONENT_DEPENDENCY = """
MATCH (source:Component {id: $component_id})-[r:DEPENDS_ON]->(target:Component {id: $depends_on_id})
DELETE r
"""

GET_COMPONENT_DEPENDENCIES = """
MATCH (c:Component {id: $component_id})-[:DEPENDS_ON]->(dep:Component)
RETURN dep
"""

GET_COMPONENT_DEPENDENTS = """
MATCH (c:Component {id: $component_id})<-[:DEPENDS_ON]-(dependent:Component)
RETURN dependent
"""

# ---------------------------------------------------------------------------
# Epic queries
# ---------------------------------------------------------------------------

CREATE_EPIC = """
CREATE (e:Epic {
    id: $id,
    name: $name,
    description: $description,
    objective_id: $objective_id,
    status: $status,
    created_at: $created_at,
    updated_at: $updated_at
})
"""

GET_EPIC = """
MATCH (e:Epic {id: $id})
RETURN e
"""

LIST_EPICS = """
MATCH (e:Epic)
RETURN e
ORDER BY e.created_at DESC
"""

UPDATE_EPIC = """
MATCH (e:Epic {id: $id})
SET e += $updates
SET e.updated_at = $updated_at
RETURN e
"""

DELETE_EPIC = """
MATCH (e:Epic {id: $id})
DETACH DELETE e
"""

LINK_ISSUE_TO_EPIC = """
MATCH (i:Issue {id: $issue_id})
MATCH (e:Epic {id: $epic_id})
MERGE (i)-[:PART_OF]->(e)
"""

# ---------------------------------------------------------------------------
# Objective queries
# ---------------------------------------------------------------------------

CREATE_OBJECTIVE = """
CREATE (o:Objective {
    id: $id,
    name: $name,
    description: $description,
    status: $status,
    quarter: $quarter,
    created_at: $created_at,
    updated_at: $updated_at
})
"""

GET_OBJECTIVE = """
MATCH (o:Objective {id: $id})
RETURN o
"""

LIST_OBJECTIVES = """
MATCH (o:Objective)
RETURN o
ORDER BY o.created_at DESC
"""

UPDATE_OBJECTIVE = """
MATCH (o:Objective {id: $id})
SET o += $updates
SET o.updated_at = $updated_at
RETURN o
"""

DELETE_OBJECTIVE = """
MATCH (o:Objective {id: $id})
DETACH DELETE o
"""

LINK_EPIC_TO_OBJECTIVE = """
MATCH (e:Epic {id: $epic_id})
MATCH (o:Objective {id: $objective_id})
MERGE (e)-[:CONTRIBUTES_TO]->(o)
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
  AND ($project IS NULL OR (c IS NOT NULL AND c.project = $project))
OPTIONAL MATCH (i)-[:DEPENDS_ON]->(dep:Issue)
OPTIONAL MATCH (i)<-[:DEPENDS_ON]-(blocked:Issue)
WITH i, collect(DISTINCT dep.id) AS dep_ids, collect(DISTINCT blocked.id) AS blocked_ids
RETURN i, dep_ids, blocked_ids
ORDER BY i.created_at DESC
"""

# BFS for Impact Analysis (optimized)
# Uses index lookups and limits traversal depth
IMPACT_ANALYSIS_BFS = """
// Find all issues transitively affected by an issue
MATCH path = (start:Issue {id: $issue_id})-[:DEPENDS_ON*1..3]->(affected:Issue)
WHERE affected.status <> 'CLOSED'
WITH start, affected, length(path) AS distance
ORDER BY distance
WITH start, collect({issue: affected, distance: distance}) AS affected_issues
RETURN start.id AS issue_id,
       size(affected_issues) AS total_affected,
       [a IN affected_issues WHERE a.distance = 1 | a.issue.id] AS directly_affected,
       [a IN affected_issues WHERE a.distance > 1 | a.issue.id] AS transitively_affected,
       affected_issues AS all_affected
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

# ---------------------------------------------------------------------------
# Cost Analytics queries
# ---------------------------------------------------------------------------

GET_COST_PER_COMPONENT = """
MATCH (i:Issue)-[:BELONGS_TO]->(c:Component)
WHERE i.status = 'CLOSED' AND i.actual_hours IS NOT NULL AND i.hourly_rate_tier IS NOT NULL
WITH c, i.actual_hours AS hours, i.hourly_rate_tier AS tier
WITH c, COLLECT({hours: hours, tier: tier}) AS issue_data
RETURN c.id AS component_id, c.name AS component_name,
       SUM(CASE WHEN 'JUNIOR' THEN hours * 75.0
               WHEN 'SENIOR' THEN hours * 125.0
               WHEN 'STAFF' THEN hours * 175.0
               WHEN 'PRINCIPAL' THEN hours * 250.0
               ELSE 0.0 END) AS actual_cost,
       SUM(CASE WHEN 'JUNIOR' THEN hours * 75.0
               WHEN 'SENIOR' THEN hours * 125.0
               WHEN 'STAFF' THEN hours * 175.0
               WHEN 'PRINCIPAL' THEN hours * 250.0
               ELSE 0.0 END) / NULLIF(SUM(hours), 0) AS avg_hourly_rate,
       SUM(hours) AS total_hours,
       COUNT(*) AS issue_count
ORDER BY actual_cost DESC
"""

GET_COST_PER_EPIC = """
MATCH (i:Issue)-[:PART_OF]->(e:Epic)
WHERE i.status = 'CLOSED' AND i.actual_hours IS NOT NULL AND i.hourly_rate_tier IS NOT NULL
WITH e, i.actual_hours AS hours, i.hourly_rate_tier AS tier
WITH e, COLLECT({hours: hours, tier: tier}) AS issue_data
RETURN e.id AS epic_id, e.name AS epic_name,
       SUM(CASE WHEN 'JUNIOR' THEN hours * 75.0
               WHEN 'SENIOR' THEN hours * 125.0
               WHEN 'STAFF' THEN hours * 175.0
               WHEN 'PRINCIPAL' THEN hours * 250.0
               ELSE 0.0 END) AS actual_cost,
       SUM(hours) AS total_hours,
       COUNT(*) AS issue_count
ORDER BY actual_cost DESC
"""

GET_COST_PER_PROJECT = """
MATCH (i:Issue)-[:BELONGS_TO]->(c:Component)-[:BELONGS_TO]->(p:Project)
WHERE i.status = 'CLOSED' AND i.actual_hours IS NOT NULL AND i.hourly_rate_tier IS NOT NULL
WITH p, i.actual_hours AS hours, i.hourly_rate_tier AS tier
WITH p, COLLECT({hours: hours, tier: tier}) AS issue_data
RETURN p.id AS project_id, p.name AS project_name,
       SUM(CASE WHEN 'JUNIOR' THEN hours * 75.0
               WHEN 'SENIOR' THEN hours * 125.0
               WHEN 'STAFF' THEN hours * 175.0
               WHEN 'PRINCIPAL' THEN hours * 250.0
               ELSE 0.0 END) AS actual_cost,
       SUM(hours) AS total_hours,
       COUNT(*) AS issue_count
ORDER BY actual_cost DESC
"""

GET_COST_SUMMARY = """
MATCH (i:Issue)
WHERE i.status = 'CLOSED' AND i.actual_hours IS NOT NULL AND i.hourly_rate_tier IS NOT NULL
WITH i.actual_hours AS hours, i.hourly_rate_tier AS tier
RETURN SUM(CASE WHEN 'JUNIOR' THEN hours * 75.0
              WHEN 'SENIOR' THEN hours * 125.0
              WHEN 'STAFF' THEN hours * 175.0
              WHEN 'PRINCIPAL' THEN hours * 250.0
              ELSE 0.0 END) AS total_actual_cost,
       SUM(hours) AS total_hours,
       COUNT(*) AS total_issues_closed
"""

# ---------------------------------------------------------------------------
# Deployment queries
# ---------------------------------------------------------------------------

CREATE_DEPLOYMENT = """
CREATE (d:Deployment {
    id: $id,
    commit_sha: $commit_sha,
    environment_name: $environment_name,
    deployed_at: $deployed_at,
    issue_ids: $issue_ids,
    channel: $channel,
    deployed_by: $deployed_by
})
WITH d
MATCH (i:Issue)
WHERE i.id IN $issue_ids
CREATE (i)-[:RELEASED_IN]->(d)
RETURN d
"""

GET_DEPLOYMENTS = """
MATCH (d:Deployment)
WHERE ($environment_name IS NULL OR d.environment_name = $environment_name)
RETURN d
ORDER BY d.deployed_at DESC
LIMIT $limit
"""

GET_DEPLOYMENT_BY_COMMIT = """
MATCH (d:Deployment {commit_sha: $commit_sha})
RETURN d
"""

GET_ISSUES_DEPLOYMENTS = """
MATCH (i:Issue {id: $issue_id})-[:RELEASED_IN]->(d:Deployment)
RETURN d
ORDER BY d.deployed_at DESC
"""

GET_DEPLOYMENT_ISSUES = """
MATCH (d:Deployment {id: $deployment_id})-[:RELEASED_IN]->(i:Issue)
RETURN i
"""

# ---------------------------------------------------------------------------
# Vector Search queries
# ---------------------------------------------------------------------------

SEARCH_BY_EMBEDDING = """
MATCH (i:Issue)
WHERE i.description_embedding IS NOT NULL
WITH i, apoc.algo.similarity(i.description_embedding, $embedding, 'cosine') AS score
WHERE score > $threshold
RETURN i.id AS issue_id, i.title AS title, score
ORDER BY score DESC
LIMIT $limit
"""

FIND_SIMILAR_ISSUES = """
MATCH (i:Issue {id: $issue_id})
WHERE i.description_embedding IS NOT NULL
WITH i
MATCH (other:Issue)
WHERE other.id <> i.id AND other.description_embedding IS NOT NULL
WITH other, apoc.algo.similarity(i.description_embedding, other.description_embedding, 'cosine') AS score
WHERE score > $threshold
RETURN other.id AS issue_id, other.title AS title, score
ORDER BY score DESC
LIMIT $limit
"""

UPDATE_ISSUE_EMBEDDING = """
MATCH (i:Issue {id: $id})
SET i.description_embedding = $embedding
"""
