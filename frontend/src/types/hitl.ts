export type HITLRequestSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
export type HITLRequestStatus = 'pending' | 'approved' | 'rejected' | 'modified'
export type HITLRequestType = 'code_change' | 'schema_migration' | 'delete_operation' | 'deploy' | 'config_change'

export interface HITLRequestDiff {
  filename: string
  content: string
}

export interface HITLRequestImpact {
  totalAffected: number
  directDeps: number
  transitiveDeps: number
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  affectedComponents: string[]
}

export interface HITLRequest {
  id: string
  title: string
  description: string
  type: HITLRequestType
  severity: HITLRequestSeverity
  status: HITLRequestStatus
  agentId: string
  agentName: string
  agentAvatar: string
  issueId: string
  issueTitle: string
  component: string
  command: string
  target?: string
  diffs: HITLRequestDiff[]
  impact: HITLRequestImpact
  createdAt: string
  reviewedAt?: string
  reviewedBy?: string
  feedback?: string
}
