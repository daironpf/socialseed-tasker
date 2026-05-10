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
    "CREATE CONSTRAINT componentId IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT projectId IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT project_slug IF NOT EXISTS FOR (p:Project) REQUIRE p.slug IS UNIQUE",
    "CREATE CONSTRAINT code_file_id IF NOT EXISTS FOR (f:CodeFile) REQUIRE f.id IS UNIQUE",
    "CREATE CONSTRAINT code_symbol_id IF NOT EXISTS FOR (s:CodeSymbol) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT code_import_id IF NOT EXISTS FOR (i:CodeImport) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT reasoning_id IF NOT EXISTS FOR (r:ReasoningNode) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT agentId IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT user_email IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE",
    "CREATE CONSTRAINT commit_sha IF NOT EXISTS FOR (c:Commit) REQUIRE c.sha IS UNIQUE",
    "CREATE CONSTRAINT rag_embedding_id IF NOT EXISTS FOR (r:RAGEmbedding) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT label_id IF NOT EXISTS FOR (l:Label) REQUIRE l.id IS UNIQUE",
    "CREATE CONSTRAINT policy_id IF NOT EXISTS FOR (p:Policy) REQUIRE p.id IS UNIQUE",
]

SCHEMA_INDEXES = [
    "CREATE INDEX issue_status IF NOT EXISTS FOR (i:Issue) ON (i.status)",
    "CREATE INDEX issue_component IF NOT EXISTS FOR (i:Issue) ON (i.componentId)",
    "CREATE INDEX issue_priority IF NOT EXISTS FOR (i:Issue) ON (i.priority)",
    "CREATE INDEX commit_timestamp IF NOT EXISTS FOR (c:Commit) ON (c.timestamp)",
    "CREATE INDEX issue_labels IF NOT EXISTS FOR (i:Issue) ON i.labels",
    "CREATE INDEX issue_createdAt IF NOT EXISTS FOR (i:Issue) ON (i.createdAt)",
    "CREATE INDEX issue_project IF NOT EXISTS FOR (i:Issue) ON (i.project)",
    "CREATE INDEX component_name IF NOT EXISTS FOR (c:Component) ON (c.name)",
    "CREATE INDEX component_project IF NOT EXISTS FOR (c:Component) ON (c.project)",
    "CREATE INDEX label_name IF NOT EXISTS FOR (l:Label) ON (l.name)",
    "CREATE INDEX deployment_commit IF NOT EXISTS FOR (d:Deployment) ON (d.commitSha)",
    "CREATE INDEX deployment_environment IF NOT EXISTS FOR (d:Deployment) ON (d.environment)",
    "CREATE INDEX code_file_path IF NOT EXISTS FOR (f:CodeFile) ON (f.path)",
    "CREATE INDEX code_file_name IF NOT EXISTS FOR (f:CodeFile) ON (f.name)",
    "CREATE INDEX code_file_repo IF NOT EXISTS FOR (f:CodeFile) ON (f.repositoryPath)",
    "CREATE INDEX code_symbol_name IF NOT EXISTS FOR (s:CodeSymbol) ON (s.name)",
    "CREATE INDEX code_symbol_type IF NOT EXISTS FOR (s:CodeSymbol) ON (s.symbolType)",
    "CREATE INDEX code_symbol_file IF NOT EXISTS FOR (s:CodeSymbol) ON (s.fileId)",
    "CREATE INDEX code_import_file IF NOT EXISTS FOR (i:CodeImport) ON (i.fileId)",
    "CREATE INDEX reasoning_issue IF NOT EXISTS FOR (r:ReasoningNode) ON (r.issueId)",
    "CREATE INDEX reasoning_type IF NOT EXISTS FOR (r:ReasoningNode) ON (r.decisionType)",
    "CREATE INDEX reasoning_createdAt IF NOT EXISTS FOR (r:ReasoningNode) ON (r.createdAt)",
    "CREATE INDEX agent_id_idx IF NOT EXISTS FOR (a:Agent) ON (a.id)",
    "CREATE INDEX agent_role IF NOT EXISTS FOR (a:Agent) ON (a.role)",
    "CREATE INDEX user_username IF NOT EXISTS FOR (u:User) ON (u.username)",
    "CREATE INDEX user_role IF NOT EXISTS FOR (u:User) ON (u.role)",
    "CREATE INDEX policy_name IF NOT EXISTS FOR (p:Policy) ON (p.name)",
    "CREATE VECTOR INDEX issue_embeddings IF NOT EXISTS FOR (i:Issue) ON (i.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}",
    "CREATE VECTOR INDEX rag_content_index IF NOT EXISTS FOR (r:RAGEmbedding) ON (r.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}",
    "CREATE INDEX code_calls IF NOT EXISTS FOR ()-[r:CALLS]->() ON (r.timestamp)",
    "CREATE INDEX code_depends IF NOT EXISTS FOR ()-[r:DEPENDS_ON]->(i:Issue) ON (i.timestamp)",
    "CREATE INDEX agent_thought IF NOT EXISTS FOR ()-[r:THOUGHT]->() ON (r.timestamp)",
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
    projectId: $projectId,
    createdAt: $createdAt,
    updatedAt: $updatedAt
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

LIST_PROJECT_NODES = """
MATCH (p:Project)
RETURN p
ORDER BY p.name
"""

CREATE_PROJECT = """
MERGE (p:Project {slug: $slug})
SET p.id = $id,
    p.name = $name,
    p.description = $description,
    p.repositoryUrl = $repositoryUrl,
    p.basePackage = $basePackage,
    p.visibility = $visibility,
    p.status = $status,
    p.techStack = $techStack,
    p.mainStack = $mainStack,
    p.architectureStyle = $architectureStyle,
    p.version = $version,
    p.conventionsUrl = $conventionsUrl,
    p.conventionsRules = $conventionsRules,
    p.lastFullScan = $lastFullScan,
    p.globalStatus = $globalStatus,
    p.createdAt = $createdAt,
    p.updatedAt = $updatedAt
RETURN p
"""

PROJECT_COMPONENTS = """
MATCH (p:Project {name: $project_name})<-[:BELONGS_TO]-(c:Component)
RETURN c
ORDER BY c.name
"""

PROJECT_ISSUES = """
MATCH (p:Project {name: $project_name})<-[:BELONGS_TO]-(c:Component)<-[:BELONGS_TO]-(i:Issue)
RETURN i
ORDER BY i.createdAt DESC
"""

PROJECT_ASSIGN_AGENT = """
MATCH (p:Project {id: $projectId})
MATCH (a:Agent {id: $agentId})
MERGE (p)-[:ASSIGNED_TO]->(a)
"""

PROJECT_REMOVE_AGENT = """
MATCH (p:Project {id: $projectId})-[r:ASSIGNED_TO]->(a:Agent {id: $agentId})
DELETE r
"""

PROJECT_GET_AGENTS = """
MATCH (p:Project {id: $projectId})-[:ASSIGNED_TO]->(a:Agent)
RETURN a
ORDER BY a.name
"""

LIST_ISSUES_PAGINATED = """
MATCH (i:Issue)
USING INDEX i:Issue(status)
WHERE ($componentId IS NULL OR i.componentId = $componentId)
  AND ($statuses IS NULL OR i.status IN $statuses)
  AND ($project IS NULL OR i.project = $project)
RETURN i
ORDER BY i.createdAt DESC
SKIP $skip
LIMIT $limit
"""

COUNT_ISSUES = """
MATCH (i:Issue)
WHERE ($componentId IS NULL OR i.componentId = $componentId)
  AND ($statuses IS NULL OR i.status IN $statuses)
  AND ($project IS NULL OR i.project = $project)
RETURN count(i) as total
"""

UPDATE_COMPONENT = """
MATCH (c:Component {id: $id})
SET c += $updates
SET c.updatedAt = $updatedAt
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
MATCH (source:Component {id: $componentId})
MATCH (target:Component {id: $depends_on_id})
MERGE (source)-[:DEPENDS_ON]->(target)
"""

REMOVE_COMPONENT_DEPENDENCY = """
MATCH (source:Component {id: $componentId})-[r:DEPENDS_ON]->(target:Component {id: $depends_on_id})
DELETE r
"""

GET_COMPONENT_DEPENDENCIES = """
MATCH (c:Component {id: $componentId})-[:DEPENDS_ON]->(dep:Component)
RETURN dep
"""

GET_COMPONENT_DEPENDENTS = """
MATCH (c:Component {id: $componentId})<-[:DEPENDS_ON]-(dependent:Component)
RETURN dependent
"""

# ---------------------------------------------------------------------------
# Agent node creation
# ---------------------------------------------------------------------------

CREATE_AGENT_NODE = """
MERGE (a:Agent {id: $id})
SET a.name = $name,
    a.role = $role,
    a.status = $status,
    a.capabilities = $capabilities,
    a.createdAt = $createdAt
RETURN a
"""

# ---------------------------------------------------------------------------
# Agent specialty and domain-driven dispatching relationships
# ---------------------------------------------------------------------------

ADD_AGENT_SPECIALIST = """
MATCH (a:Agent {id: $agentId})
MATCH (c:Component {id: $componentId})
MERGE (a)-[:SPECIALIST_IN]->(c)
"""

REMOVE_AGENT_SPECIALIST = """
MATCH (a:Agent {id: $agentId})-[r:SPECIALIST_IN]->(c:Component {id: $componentId})
DELETE r
"""

GET_AGENT_SPECIALISTS = """
MATCH (a:Agent {id: $agentId})-[:SPECIALIST_IN]->(c:Component)
RETURN c
"""

GET_COMPONENT_SPECIALISTS = """
MATCH (a:Agent)-[:SPECIALIST_IN]->(c:Component {id: $componentId})
RETURN a
"""

ADD_AGENT_INTERESTED = """
MATCH (a:Agent {id: $agentId})
MATCH (l:Label {id: $label_id})
MERGE (a)-[:INTERESTED_IN]->(l)
"""

GET_AGENT_INTERESTS = """
MATCH (a:Agent {id: $agentId})-[:INTERESTED_IN]->(l:Label)
RETURN l
"""

# ---------------------------------------------------------------------------
# CodeSymbol hierarchical relationships
# ---------------------------------------------------------------------------

ADD_SYMBOL_CHILD_OF = """
MATCH (child:CodeSymbol {id: $child_id})
MATCH (parent:CodeSymbol {id: $parent_id})
MERGE (child)-[:CHILD_OF]->(parent)
"""

GET_SYMBOL_CHILDREN = """
MATCH (s:CodeSymbol {id: $symbol_id})-[:CHILD_OF]->(parent:CodeSymbol)
RETURN parent
"""

GET_SYMBOL_PARENTS = """
MATCH (s:CodeSymbol {id: $symbol_id})<-[:CHILD_OF]-(child:CodeSymbol)
RETURN child
"""

# ---------------------------------------------------------------------------
# Semantic linkage for RAG
# ---------------------------------------------------------------------------

ADD_SYMBOL_VECTOR = """
MATCH (s:CodeSymbol {id: $symbol_id})
MATCH (r:RAGEmbedding {id: $embedding_id})
MERGE (s)-[:HAS_VECTOR]->(r)
"""

GET_SYMBOL_EMBEDDINGS = """
MATCH (s:CodeSymbol {id: $symbol_id})-[:HAS_VECTOR]->(r:RAGEmbedding)
RETURN r
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
    createdAt: $createdAt,
    updatedAt: $updatedAt
})
"""

GET_EPIC = """
MATCH (e:Epic {id: $id})
RETURN e
"""

LIST_EPICS = """
MATCH (e:Epic)
RETURN e
ORDER BY e.createdAt DESC
"""

UPDATE_EPIC = """
MATCH (e:Epic {id: $id})
SET e += $updates
SET e.updatedAt = $updatedAt
RETURN e
"""

DELETE_EPIC = """
MATCH (e:Epic {id: $id})
DETACH DELETE e
"""

LINK_ISSUE_TO_EPIC = """
MATCH (i:Issue {id: $issue_id})
MATCH (e:Epic {id: $epicId})
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
    createdAt: $createdAt,
    updatedAt: $updatedAt
})
"""

GET_OBJECTIVE = """
MATCH (o:Objective {id: $id})
RETURN o
"""

LIST_OBJECTIVES = """
MATCH (o:Objective)
RETURN o
ORDER BY o.createdAt DESC
"""

UPDATE_OBJECTIVE = """
MATCH (o:Objective {id: $id})
SET o += $updates
SET o.updatedAt = $updatedAt
RETURN o
"""

DELETE_OBJECTIVE = """
MATCH (o:Objective {id: $id})
DETACH DELETE o
"""

LINK_EPIC_TO_OBJECTIVE = """
MATCH (e:Epic {id: $epicId})
MATCH (o:Objective {id: $objective_id})
MERGE (e)-[:CONTRIBUTES_TO]->(o)
"""

# ---------------------------------------------------------------------------
# Issue queries
# ---------------------------------------------------------------------------

CREATE_ISSUE = """
MATCH (c:Component {id: $componentId})
CREATE (i:Issue {
    id: $id,
    title: $title,
    description: $description,
    status: $status,
    priority: $priority,
    componentId: $componentId,
    labels: $labels,
    dependencies: $dependencies,
    blocks: $blocks,
    affects: $affects,
    createdAt: $createdAt,
    updatedAt: $updatedAt,
    closedAt: $closedAt,
    architecturalConstraints: $architecturalConstraints,
    agentWorking: $agentWorking,
    agentStartedAt: $agentStartedAt,
    agentFinishedAt: $agentFinishedAt,
    agentId: $agentId,
    reasoningLogs: $reasoningLogs,
    manifestTodo: $manifestTodo,
    manifestFiles: $manifestFiles,
    manifestNotes: $manifestNotes
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
SET i.updatedAt = $updatedAt
RETURN i
"""

CLOSE_ISSUE = """
MATCH (i:Issue {id: $id})
SET i.status = 'CLOSED', i.closedAt = $closedAt, i.updatedAt = $updatedAt
RETURN i
"""

DELETE_ISSUE = """
MATCH (i:Issue {id: $id})
DETACH DELETE i
"""

LIST_ISSUES = """
MATCH (i:Issue)
OPTIONAL MATCH (i)-[:BELONGS_TO]->(c:Component)
WHERE ($componentId IS NULL OR i.componentId = $componentId)
  AND (size($statuses) = 0 OR i.status IN $statuses)
  AND ($project IS NULL OR (c IS NOT NULL AND c.project = $project))
OPTIONAL MATCH (i)-[:DEPENDS_ON]->(dep:Issue)
OPTIONAL MATCH (i)<-[:DEPENDS_ON]-(blocked:Issue)
WITH i, collect(DISTINCT dep.id) AS dep_ids, collect(DISTINCT blocked.id) AS blocked_ids
RETURN i, dep_ids, blocked_ids
ORDER BY i.createdAt DESC
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

GET_DEPENDENCIES_BY_FILE = """
MATCH (f:CodeFile {path: $file_path})<-[:IMPORTS]-(i:CodeImport)
MATCH (target:CodeFile)
WHERE target.name = i.module OR target.path CONTAINS i.module
RETURN DISTINCT target.path as path, target.name as module
"""

GET_STALE_FILES = """
MATCH (f:CodeFile)
WHERE NOT f.path ENDS WITH '.py'
   AND NOT f.path ENDS WITH '.js'
   AND NOT f.path ENDS WITH '.ts'
RETURN f.path as stale_path
ORDER BY f.path
"""

CLEANUP_STALE_NODES = """
MATCH (f:CodeFile)
WHERE NOT file_exists(f.path)
DETACH DELETE f
WITH 1 as dummy
MATCH (s:CodeSymbol)
WHERE NOT (s)-[:BELONGS_TO]->()
DETACH DELETE s
RETURN count(*) as deleted
"""

UPDATE_ISSUE_LOCK = """
MATCH (i:Issue {id: $issue_id})
SET i.lockedUntil = $lockedUntil, i.agentWorking = true
RETURN i
"""

RELEASE_EXPIRED_LOCKS = """
MATCH (i:Issue)
WHERE i.lockedUntil < datetime()
SET i.agentWorking = false, i.lockedUntil = null
RETURN count(*) as released
"""

GET_INTERNAL_DEPENDENCIES = """
MATCH (f:CodeFile)<-[:IMPORTS]-(i:CodeImport)
MATCH (f2:CodeFile)
WHERE f2.name = i.module OR f2.path CONTAINS i.module
MERGE (f)-[r:DEPENDS_ON_INTERNAL]->(f2)
RETURN f.path as from_path, f2.path as to_path
"""

RESOLVE_INTERNAL_IMPORTS = """
MATCH (i:CodeImport)
MATCH (f:CodeFile)
WHERE f.name = i.module OR f.path CONTAINS i.module
MERGE (f)<-[:DEPENDS_ON]-(source:CodeFile)
WHERE (source)-[:IMPORTS]->(i)
RETURN count(*) as resolved
"""

GET_DEPENDENCIES = """
MATCH (source:Issue {id: $issue_id})-[:DEPENDS_ON]->(target:Issue)
RETURN target
ORDER BY target.createdAt DESC
"""

GET_DEPENDENTS = """
MATCH (target:Issue {id: $issue_id})<-[:DEPENDS_ON]-(source:Issue)
RETURN source
ORDER BY source.createdAt DESC
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
SET l.id = $id,
    l.color = $color,
    l.description = $description,
    l.createdAt = $createdAt,
    l.updatedAt = $updatedAt
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
WHERE i.status = 'CLOSED' AND i.actualHours IS NOT NULL AND i.hourlyRateTier IS NOT NULL
WITH c, i.actualHours AS hours, i.hourlyRateTier AS tier
WITH c, COLLECT({hours: hours, tier: tier}) AS issue_data
RETURN c.id AS componentId, c.name AS component_name,
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
WHERE i.status = 'CLOSED' AND i.actualHours IS NOT NULL AND i.hourlyRateTier IS NOT NULL
WITH e, i.actualHours AS hours, i.hourlyRateTier AS tier
WITH e, COLLECT({hours: hours, tier: tier}) AS issue_data
RETURN e.id AS epicId, e.name AS epic_name,
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
WHERE i.status = 'CLOSED' AND i.actualHours IS NOT NULL AND i.hourlyRateTier IS NOT NULL
WITH p, i.actualHours AS hours, i.hourlyRateTier AS tier
WITH p, COLLECT({hours: hours, tier: tier}) AS issue_data
RETURN p.id AS projectId, p.name AS project_name,
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
WHERE i.status = 'CLOSED' AND i.actualHours IS NOT NULL AND i.hourlyRateTier IS NOT NULL
WITH i.actualHours AS hours, i.hourlyRateTier AS tier
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
WHERE i.descriptionEmbedding IS NOT NULL
WITH i, apoc.algo.similarity(i.descriptionEmbedding, $embedding, 'cosine') AS score
WHERE score > $threshold
RETURN i.id AS issue_id, i.title AS title, score
ORDER BY score DESC
LIMIT $limit
"""

FIND_SIMILAR_ISSUES = """
MATCH (i:Issue {id: $issue_id})
WHERE i.descriptionEmbedding IS NOT NULL
WITH i
MATCH (other:Issue)
WHERE other.id <> i.id AND other.descriptionEmbedding IS NOT NULL
WITH other, apoc.algo.similarity(i.descriptionEmbedding, other.descriptionEmbedding, 'cosine') AS score
WHERE score > $threshold
RETURN other.id AS issue_id, other.title AS title, score
ORDER BY score DESC
LIMIT $limit
"""

UPDATE_ISSUE_EMBEDDING = """
MATCH (i:Issue {id: $id})
SET i.descriptionEmbedding = $embedding
"""

ISSUE_AFFECTS_FILE = """
MATCH (i:Issue {id: $issue_id})
MATCH (f:CodeFile)
WHERE f.path CONTAINS $file_path OR f.name = $file_path
MERGE (i)-[r:AFFECTS]->(f)
SET r.closedAt = $closedAt
RETURN i, f
"""

FIND_ISSUES_AFFECTING_FILE = """
MATCH (i:Issue)-[r:AFFECTS]->(f:CodeFile)
WHERE f.path CONTAINS $file_path OR f.name = $file_path
WHERE i.status = 'CLOSED'
RETURN i.id as issue_id, i.title as title, f.path as file_path, r.closedAt as closedAt
ORDER BY r.closedAt DESC
LIMIT toInteger($limit)
"""

ISSUE_AFFECTS_SYMBOL = """
MATCH (i:Issue {id: $issue_id})
MATCH (s:CodeSymbol {id: $symbol_id})
MERGE (i)-[r:AFFECTS]->(s)
SET r.closedAt = $closedAt
RETURN i, s
"""

FIND_ISSUES_AFFECTING_SYMBOL = """
MATCH (i:Issue)-[r:AFFECTS]->(s:CodeSymbol {name: $symbol_name})
WHERE i.status = 'CLOSED'
RETURN i.id as issue_id, i.title as title, s.name as symbol_name, r.closedAt as closedAt
ORDER BY r.closedAt DESC
LIMIT toInteger($limit)
"""

# ---------------------------------------------------------------------------
# User queries
# ---------------------------------------------------------------------------

CREATE_USER = """
CREATE (u:User {
    id: $id,
    username: $username,
    email: $email,
    role: $role,
    githubHandle: $githubHandle,
    createdAt: $createdAt,
    lastLogin: $lastLogin,
    preferences: $preferences
})
RETURN u
"""

GET_USER = """
MATCH (u:User {id: $id})
RETURN u
"""

GET_USER_BY_EMAIL = """
MATCH (u:User {email: $email})
RETURN u
"""

GET_USER_BY_USERNAME = """
MATCH (u:User {username: $username})
RETURN u
"""

UPDATE_USER = """
MATCH (u:User {id: $id})
SET u += $updates, u.updatedAt = $updatedAt
RETURN u
"""

DELETE_USER = """
MATCH (u:User {id: $id})
DETACH DELETE u
"""

LIST_USERS = """
MATCH (u:User)
WHERE ($role IS NULL OR u.role = $role)
RETURN u
ORDER BY u.username
LIMIT $limit
"""

UPDATE_LAST_LOGIN = """
MATCH (u:User {id: $id})
SET u.lastLogin = $lastLogin
RETURN u
"""

USER_MANAGES_PROJECT = """
MATCH (u:User {id: $user_id})
MATCH (p:Project {id: $projectId})
MERGE (u)-[:MANAGES]->(p)
RETURN u, p
"""

USER_VALIDATES_REASONING = """
MATCH (u:User {id: $user_id})
MATCH (r:ReasoningNode {id: $reasoning_id})
MERGE (u)-[v:VALIDATES {approved: $approved, comment: $comment, validated_at: timestamp()}]->(r)
RETURN u, r, v
"""

USER_ASSIGNED_TO_ISSUE = """
MATCH (u:User {id: $user_id})
MATCH (i:Issue {id: $issue_id})
MERGE (u)-[:ASSIGNED_TO]->(i)
RETURN u, i
"""

USER_AUTHORED_COMMIT = """
MATCH (u:User {id: $user_id})
MATCH (c:Commit {sha: $commit_sha})
MERGE (u)-[:AUTHORED]->(c)
RETURN u, c
"""

GET_USER_PROJECTS = """
MATCH (u:User {id: $user_id})-[:MANAGES]->(p:Project)
RETURN p
"""

GET_USER_ISSUES = """
MATCH (u:User {id: $user_id})-[:ASSIGNED_TO]->(i:Issue)
RETURN i
ORDER BY i.createdAt DESC
LIMIT $limit
"""

GET_USER_COMMITS = """
MATCH (u:User {id: $user_id})-[:AUTHORED]->(c:Commit)
RETURN c
ORDER BY c.timestamp DESC
LIMIT $limit
"""

# ---------------------------------------------------------------------------
# Commit queries
# ---------------------------------------------------------------------------

CREATE_COMMIT = """
CREATE (c:Commit {
    sha: $sha,
    message: $message,
    authorName: $author_name,
    authorEmail: $author_email,
    timestamp: $timestamp,
    isAiGenerated: $is_ai_generated,
    branch: $branch,
    additions: $additions,
    deletions: $deletions,
    filesChanged: $files_changed
})
RETURN c
"""

GET_COMMIT = """
MATCH (c:Commit {sha: $sha})
RETURN c
"""

LIST_COMMITS = """
MATCH (c:Commit)
WHERE ($branch IS NULL OR c.branch = $branch)
  AND ($author IS NULL OR c.authorName = $author)
  AND ($is_ai_generated IS NULL OR c.isAiGenerated = $is_ai_generated)
  AND ($since IS NULL OR c.timestamp >= $since)
  AND ($until IS NULL OR c.timestamp <= $until)
RETURN c
ORDER BY c.timestamp DESC
SKIP $skip
LIMIT $limit
"""

DELETE_COMMIT = """
MATCH (c:Commit {sha: $sha})
DETACH DELETE c
"""

LINK_COMMIT_TO_AGENT = """
MATCH (c:Commit {sha: $sha})
MATCH (a:Agent {id: $agentId})
MERGE (a)-[:AUTHORED]->(c)
RETURN a, c
"""

LINK_COMMIT_TO_USER = """
MATCH (c:Commit {sha: $sha})
MATCH (u:User {id: $user_id})
MERGE (u)-[:AUTHORED]->(c)
RETURN u, c
"""

LINK_COMMIT_TO_ISSUE = """
MATCH (c:Commit {sha: $sha})
MATCH (i:Issue {id: $issue_id})
MERGE (i)-[:RESOLVED_BY]->(c)
RETURN i, c
"""

LINK_COMMIT_TO_FILE = """
MATCH (c:Commit {sha: $sha})
MATCH (f:CodeFile {path: $file_path})
MERGE (c)-[r:MODIFIED {type: $change_type}]->(f)
RETURN c, f, r
"""

LINK_COMMIT_TO_REASONING = """
MATCH (c:Commit {sha: $sha})
MATCH (r:ReasoningNode {id: $reasoning_id})
MERGE (r)-[:RESULTED_IN]->(c)
RETURN r, c
"""

GET_COMMITS_FOR_ISSUE = """
MATCH (i:Issue {id: $issue_id})-[:RESOLVED_BY]->(c:Commit)
RETURN c
ORDER BY c.timestamp DESC
LIMIT $limit
"""

GET_COMMITS_FOR_FILE = """
MATCH (c:Commit)-[r:MODIFIED]->(f:CodeFile)
WHERE f.path = $file_path OR f.name = $file_path
RETURN c, r.type as change_type
ORDER BY c.timestamp DESC
LIMIT $limit
"""

GET_AUTHOR_STATS = """
MATCH (c:Commit)
WHERE ($since IS NULL OR c.timestamp >= $since)
OPTIONAL MATCH (a:Agent)-[:AUTHORED]->(c)
OPTIONAL MATCH (u:User)-[:AUTHORED]->(c)
RETURN 
    count(c) as total_commits,
    sum(c.additions) as total_additions,
    sum(c.deletions) as total_deletions,
    sum(c.filesChanged) as total_files,
    collect(DISTINCT CASE WHEN a IS NOT NULL THEN a.name END) as ai_authors,
    collect(DISTINCT CASE WHEN u IS NOT NULL THEN u.name END) as human_authors,
    count(DISTINCT CASE WHEN c.isAiGenerated = true THEN c END) as ai_commits,
    count(DISTINCT CASE WHEN c.isAiGenerated = false THEN c END) as human_commits
"""

GET_COMMITS_FOR_REASONING = """
MATCH (r:ReasoningNode {id: $reasoning_id})-[:RESULTED_IN]->(c:Commit)
RETURN c
ORDER BY c.timestamp DESC
LIMIT $limit
"""

# ---------------------------------------------------------------------------
# Policy queries
# ---------------------------------------------------------------------------

CREATE_POLICY = """
CREATE (p:Policy {
    id: $id,
    name: $name,
    description: $description,
    rules: $rules,
    target_scope: $target_scope,
    logic_definition: $logic_definition,
    remediation_strategy: $remediation_strategy,
    autofix_template: $autofix_template,
    is_active: $is_active,
    createdAt: $createdAt,
    updatedAt: $updatedAt
})
RETURN p
"""

GET_POLICY = """
MATCH (p:Policy {id: $id})
RETURN p
"""

GET_POLICY_BY_NAME = """
MATCH (p:Policy {name: $name})
RETURN p
"""

UPDATE_POLICY = """
MATCH (p:Policy {id: $id})
SET p += $updates, p.updatedAt = $updatedAt
RETURN p
"""

DELETE_POLICY = """
MATCH (p:Policy {id: $id})
DETACH DELETE p
"""

LIST_POLICIES = """
MATCH (p:Policy)
WHERE ($severity IS NULL OR p.severity = $severity)
  AND ($target_scope IS NULL OR p.target_scope = $target_scope)
  AND ($is_active IS NULL OR p.is_active = $is_active)
RETURN p
ORDER BY p.name
LIMIT $limit
"""

LINK_POLICY_TO_PROJECT = """
MATCH (p:Policy {id: $policy_id})
MATCH (proj:Project {id: $projectId})
MERGE (proj)-[:ENFORCES]->(p)
RETURN proj, p
"""

LINK_POLICY_TO_AGENT = """
MATCH (p:Policy {id: $policy_id})
MATCH (a:Agent {id: $agentId})
MERGE (a)-[:MUST_COMPLY_WITH]->(p)
RETURN a, p
"""

LINK_POLICY_TO_COMPONENT = """
MATCH (p:Policy {id: $policy_id})
MATCH (c:Component {id: $componentId})
MERGE (p)-[:APPLIES_TO]->(c)
RETURN p, c
"""

GET_POLICIES_FOR_PROJECT = """
MATCH (proj:Project {id: $projectId})-[:ENFORCES]->(p:Policy)
RETURN p
ORDER BY p.name
LIMIT $limit
"""

GET_POLICIES_FOR_AGENT = """
MATCH (a:Agent {id: $agentId})-[:MUST_COMPLY_WITH]->(p:Policy)
RETURN p
ORDER BY p.name
LIMIT $limit
"""

GET_POLICIES_FOR_COMPONENT = """
MATCH (p:Policy)-[:APPLIES_TO]->(c:Component {id: $componentId})
RETURN p
ORDER BY p.name
LIMIT $limit
"""

POLICY_VIOLATES_COMMIT = """
MATCH (p:Policy {id: $policy_id})
MATCH (c:Commit {sha: $commit_sha})
MERGE (c)-[:VIOLATES]->(p)
RETURN c, p
"""

REASONING_VALIDATED_AGAINST_POLICY = """
MATCH (r:ReasoningNode {id: $reasoning_id})
MATCH (p:Policy {id: $policy_id})
MERGE (r)-[:VALIDATED_AGAINST]->(p)
RETURN r, p
"""

GET_POLICY_VIOLATIONS = """
MATCH (c:Commit)-[:VIOLATES]->(p:Policy {id: $policy_id})
RETURN c, p
ORDER BY c.timestamp DESC
LIMIT $limit
"""
