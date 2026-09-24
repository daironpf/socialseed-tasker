export type AuditLogEventType =
  | 'status_change'
  | 'hitl_decision'
  | 'policy_violation'
  | 'agent_run'
  | 'login'
  | 'export'
  | 'governance_override'
  | 'pii_redaction'

export type AuditLogSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface AuditLogEntry {
  id: string
  timestamp: string
  actor: string
  actorType: 'human' | 'agent' | 'system'
  agent?: string
  eventType: AuditLogEventType
  severity: AuditLogSeverity
  resource: string
  action: string
  ip?: string
  details?: Record<string, string>
}

export interface AuditChainBlock {
  id: string
  label: string
  count: number
  hash: string
  previousHash: string
  timestamp: string
  verified: boolean
}

export interface AuditLogFilters {
  dateFrom: string
  dateTo: string
  actor: string
  agent: string
  eventType: string
  severity: string
  search: string
}

export const AUDIT_EVENT_TYPES: AuditLogEventType[] = [
  'status_change',
  'hitl_decision',
  'policy_violation',
  'agent_run',
  'login',
  'export',
  'governance_override',
  'pii_redaction',
]

export const AUDIT_SEVERITIES: AuditLogSeverity[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
