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
  description?: string
  project: string
}

export interface CausalLink {
  issue_id: string
  issue_title: string
  confidence: number
  reasons: string[]
  graph_distance: number
}

export interface ImpactIssueSummary {
  id: string
  title: string
  status: string
}

export interface ImpactAnalysis {
  issue_id: string
  directly_affected: ImpactIssueSummary[]
  transitively_affected: ImpactIssueSummary[]
  blocked_issues: ImpactIssueSummary[]
  affected_components: string[]
  risk_level: string
}
