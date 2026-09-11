export enum IssueStatus {
  OPEN = 'OPEN',
  IN_PROGRESS = 'IN_PROGRESS',
  CLOSED = 'CLOSED',
  BLOCKED = 'BLOCKED',
}

export enum IssuePriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

export interface Issue {
  id: string
  title: string
  description: string
  status: string
  priority: string
  component_id: string
  assignee?: string
  created_by?: string
  labels: string[]
  dependencies: string[]
  blocks: string[]
  affects: string[]
  created_at: string
  updated_at: string
  closed_at: string | null
  architectural_constraints: string[]
  agent_working?: boolean
}

export interface Component {
  id: string
  name: string
  alias?: string
  description: string | null
  project: string
  created_at: string
  updated_at: string
}

export interface PaginationMeta {
  page: number
  limit: number
  total: number
  has_next: boolean
  has_prev: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: PaginationMeta
}

export interface ErrorDetail {
  code: string
  message: string
  details: Record<string, unknown>
}

export interface Meta {
  timestamp: string
  request_id: string | null
}

export interface APIResponse<T> {
  data: T | null
  error: ErrorDetail | null
  meta: Meta
}

export interface IssueCreateRequest {
  title: string
  description?: string
  priority?: string
  component_id: string
  labels?: string[]
  architectural_constraints?: string[]
}

export interface IssueUpdateRequest {
  title?: string
  description?: string
  priority?: string
  status?: string
  component_id?: string
  labels?: string[]
  architectural_constraints?: string[]
}

export interface DependencyRequest {
  depends_on_id: string
}

export interface ComponentCreateRequest {
  name: string
  alias?: string
  description?: string
  project: string
}

export interface CausalLink {
  issue_id: string
  issue_title: string
  issue_status: string
  confidence: number
  reasons: string[]
  graph_distance: number
}

export interface ImpactIssueSummary {
  id: string
  title: string
  status: string
  level?: number
}

export interface ImpactAnalysis {
  issue_id: string
  issue_title: string
  issue_status: string
  directly_affected: ImpactIssueSummary[]
  transitively_affected: ImpactIssueSummary[]
  blocked_issues: ImpactIssueSummary[]
  affected_components: string[]
  risk_level: string
  graph_depth: number
  total_affected: number
}

export interface Policy {
  id: string
  name: string
  description: string
  rules: any[]
  target_scope: string
  logic_definition?: string
  remediation_strategy?: string
  autofix_template?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface TestFailure {
  test_id: string
  test_name: string
  error_message: string
  component: string
  failed_at: string
  labels: string[]
}

export interface DependencyEdge {
  from: string
  to: string
  type: 'blocks' | 'depends_on'
}

export interface DependencyNode {
  id: string
  label: string
  status: string
  priority: string
  component: string
}

export interface DependencyGraph {
  nodes: DependencyNode[]
  edges: DependencyEdge[]
  summary: {
    total_nodes: number
    total_edges: number
    blocked_issues: number
    critical_path_length: number
    most_connected_node: string
  }
}

export interface AgentLog {
  timestamp: string
  type: 'reasoning' | 'progress' | 'files' | 'debt'
  content_markdown: string
}

export interface AgentLogsBundle {
  issue_id: string
  agent_id?: string
  logs: AgentLog[]
}

export type ConstraintCategory = 'ARCHITECTURE' | 'TECHNOLOGY' | 'NAMING' | 'PATTERNS' | 'DEPENDENCIES'
export type ConstraintSeverity = 'HARD' | 'SOFT'

export interface ConstraintRule {
  type: string
  target?: string
  target_field?: string
  max_value?: number
  min_count?: number
  pattern?: string
  blocked_values?: string[]
  label_component_map?: Record<string, string>
  condition_field?: string
  condition_value?: string
  min_reviews?: number
  message?: string
  metric?: string
}

export interface Constraint {
  id: string
  name: string
  description: string
  category: ConstraintCategory
  severity: ConstraintSeverity
  scope: string
  rule: ConstraintRule
  logic: string
  remediation: string
  auto_fix: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ConstraintCreateRequest {
  name: string
  description?: string
  category?: ConstraintCategory
  severity?: ConstraintSeverity
  scope?: string
  rule?: ConstraintRule
  logic?: string
  remediation?: string
  auto_fix?: boolean
}

export interface ConstraintViolation {
  constraint_id: string
  constraint_name: string
  severity: ConstraintSeverity
  category: ConstraintCategory
  message: string
  remediation: string
}

export interface ValidationResult {
  valid: boolean
  hard_violations: number
  soft_violations: number
  total_violations: number
  violations: ConstraintViolation[]
  checked_constraints: number
}

export interface ServiceStatus {
  status: string
  latency_ms?: number
  uptime_seconds?: number
  version?: string
  last_check?: string
  active_count?: number
  queue_size?: number
}

export interface SystemHealth {
  status: string
  timestamp: string
  services: {
    neo4j: ServiceStatus
    api: ServiceStatus
    workers: ServiceStatus
  }
  metrics: {
    total_issues: number
    blocked_issues: number
    total_components: number
    agents_working: number
    total_users: number
    total_constraints: number
    active_constraints: number
  }
}

export interface SyncQueueItem {
  id: string
  action: string
  resource: string
  resource_id: string
  created_at: string
  status: string
  retry_count: number
}

export interface SyncQueue {
  pending: number
  queue: SyncQueueItem[]
  last_sync_at: string
  github_connected: boolean
}
