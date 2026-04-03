# Issue #12: Implement Causal Traceability - Root Cause Analysis

## Description

Implement the causal traceability feature that links failed tests (from `socialseed-e2e`) to recently closed issues to find the "Root Cause" using graph proximity analysis. This is a key differentiator of the SocialSeed Tasker system.

### Requirements

#### Root Cause Analysis Engine

Create a new module or extend `core/project_analysis/analyzer.py` with root cause analysis capabilities:

```python
class RootCauseAnalyzer:
    def __init__(self, repository: TaskRepositoryInterface):
        self.repository = repository
    
    def find_root_cause(self, failed_test_id: str, closed_issues: list[Issue]) -> list[CausalLink]:
        """
        Find which recently closed issues are most likely responsible for a test failure.
        
        Uses graph proximity analysis to rank potential root causes:
        1. Direct dependency links (issue -> component that was modified)
        2. Shared component analysis (issue and test affect same component)
        3. Temporal proximity (recently closed issues are more likely culprits)
        4. Label/keyword matching between test failure and issue description
        """
        ...
    
    def analyze_impact(self, issue_id: UUID) -> ImpactAnalysis:
        """
        Analyze what other issues and components would be affected if this issue changes.
        
        Traverses the graph to find:
        - All issues that DEPENDS_ON this issue
        - All issues that this issue BLOCKS
        - All issues that this issue AFFECTS
        - Transitive impact (issues affected by affected issues)
        """
        ...
    
    def get_proximity_score(self, issue: Issue, failed_test: TestFailure) -> float:
        """
        Calculate a proximity score indicating how likely this issue is the root cause.
        
        Scoring factors:
        - Direct graph distance (shortest path in dependency graph)
        - Component overlap (same component = higher score)
        - Temporal recency (more recently closed = higher score)
        - Semantic similarity (keyword/label overlap)
        """
        ...
```

#### Data Models

```python
class TestFailure(BaseModel):
    test_id: str
    test_name: str
    error_message: str
    stack_trace: str
    component: str
    timestamp: datetime
    labels: list[str] = []

class CausalLink(BaseModel):
    issue: Issue
    confidence: float  # 0.0 to 1.0
    reasons: list[str]  # Why this issue is suspected
    graph_distance: int  # Number of hops from test to issue
    temporal_distance: timedelta  # Time between issue close and test failure

class ImpactAnalysis(BaseModel):
    issue_id: UUID
    directly_affected: list[Issue]
    transitively_affected: list[Issue]
    blocked_issues: list[Issue]
    affected_components: list[Component]
    risk_level: RiskLevel  # LOW, MEDIUM, HIGH, CRITICAL
```

#### Neo4j Queries for Root Cause Analysis

```cypher
// Find recently closed issues in the same component as a failed test
MATCH (i:Issue {component_id: $component_id})
WHERE i.status = 'CLOSED'
  AND i.closed_at > datetime() - duration('P7D')
RETURN i ORDER BY i.closed_at DESC

// Find dependency chain from issue to affected components
MATCH path = (i:Issue {id: $issue_id})-[:DEPENDS_ON|BLOCKS|AFFECTS*1..5]->(affected:Issue)
RETURN path, length(path) as distance
ORDER BY distance

// Calculate graph proximity between two issues
MATCH (a:Issue {id: $issue_a}), (b:Issue {id: $issue_b})
MATCH path = shortestPath((a)-[:DEPENDS_ON|BLOCKS|AFFECTS*]-(b))
RETURN length(path) as distance
```

#### Integration Points

**CLI Commands:**
- `analyze root-cause <test_failure>` - Find root cause of a test failure
- `analyze impact <issue_id>` - Show impact analysis for an issue
- `analyze affected <issue_id>` - Show all transitively affected issues

**API Endpoints:**
- `POST /api/v1/analyze/root-cause` - Submit test failure, get potential root causes
- `GET /api/v1/analyze/impact/{issue_id}` - Get impact analysis for an issue
- `GET /api/v1/analyze/affected/{issue_id}` - Get all affected issues

#### Scoring Algorithm

The proximity score should combine multiple factors:

```python
def calculate_proximity_score(graph_distance, temporal_distance, component_overlap, semantic_similarity):
    weights = {
        'graph_distance': 0.35,      # Most important factor
        'temporal_distance': 0.25,   # Recently closed issues are more suspicious
        'component_overlap': 0.25,   # Same component is a strong signal
        'semantic_similarity': 0.15  # Keyword matching as supporting evidence
    }
    
    graph_score = max(0, 1 - (graph_distance * 0.2))  # Distance 0 = 1.0, Distance 5 = 0.0
    temporal_score = exp(-temporal_days / 7)  # Exponential decay over weeks
    component_score = 1.0 if component_overlap else 0.0
    semantic_score = semantic_similarity  # Already 0.0 to 1.0
    
    return sum(weights[k] * scores[k] for k in weights)
```

### Requirements
- Core analysis logic must be pure Python in `core/`
- Neo4j queries for graph traversal go in `storage/graph_database/`
- Results must be ranked by confidence score
- Must support configurable time windows (default: 7 days)
- Must support configurable maximum graph distance (default: 5 hops)
- Analysis results must include explanations for why each issue was flagged

### Business Value

Causal traceability is the killer feature of SocialSeed Tasker. When tests fail, developers waste hours figuring out what changed. By leveraging the graph of issue dependencies and temporal data, the system can pinpoint the most likely root cause in seconds. This directly addresses the "Infinite Context" and "Architectural Governance" goals of the SocialSeed Ecosystem.

## Status: COMPLETED
