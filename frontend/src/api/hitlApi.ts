import client from './client'
import type { APIResponse } from '@/types'
import type {
  HITLRequest,
  HITLRequestDiff,
  HITLRequestImpact,
  HITLRequestSeverity,
  HITLRequestStatus,
  HITLRequestType,
} from '@/types/hitl'

type Wire = Record<string, unknown>

const STATUSES: HITLRequestStatus[] = [
  'pending',
  'approved',
  'rejected',
  'revoked',
  'expired',
]
const SEVERITIES: HITLRequestSeverity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
const TYPES: HITLRequestType[] = [
  'code_change',
  'schema_migration',
  'delete_operation',
  'deploy',
  'config_change',
]

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {}
}

function asSeverity(value: unknown): HITLRequestSeverity {
  return SEVERITIES.includes(value as HITLRequestSeverity)
    ? (value as HITLRequestSeverity)
    : 'MEDIUM'
}

function asDiff(value: unknown): HITLRequestDiff | null {
  const raw = asRecord(value)
  const filename = typeof raw.filename === 'string' ? raw.filename : ''
  const content = typeof raw.content === 'string' ? raw.content : ''
  return filename || content ? { filename: filename || 'change', content } : null
}

function asImpact(value: unknown): HITLRequestImpact {
  const raw = asRecord(value)
  const affected = Array.isArray(raw.affectedComponents)
    ? raw.affectedComponents.map(String)
    : []
  return {
    totalAffected: Number(raw.totalAffected ?? affected.length) || 0,
    directDeps: Number(raw.directDeps ?? 0) || 0,
    transitiveDeps: Number(raw.transitiveDeps ?? 0) || 0,
    riskLevel: asSeverity(raw.riskLevel),
    affectedComponents: affected,
  }
}

/** Backend approval row (snake_case) -> HITL UI model. */
export function normalizeApproval(raw: Wire): HITLRequest {
  const metadata = asRecord(raw.request_metadata)
  const status = STATUSES.includes(raw.status as HITLRequestStatus)
    ? (raw.status as HITLRequestStatus)
    : 'pending'
  const type = TYPES.includes(metadata.type as HITLRequestType)
    ? (metadata.type as HITLRequestType)
    : 'code_change'
  const diffs = Array.isArray(metadata.diffs)
    ? metadata.diffs.map(asDiff).filter((diff): diff is HITLRequestDiff => diff !== null)
    : []
  const decidedAt = raw.decided_at ?? raw.revoked_at
  return {
    id: String(raw.id ?? ''),
    title: String(metadata.title ?? raw.expected_effect ?? 'Agent action approval'),
    description: String(metadata.description ?? ''),
    type,
    severity: asSeverity(metadata.severity),
    status,
    agentId: String(raw.agent_id ?? ''),
    agentName: String(raw.agent_id ?? 'agent'),
    agentAvatar: '🤖',
    issueId: String(raw.issue_id ?? ''),
    issueTitle: String(metadata.issue_title ?? ''),
    component: String(metadata.component ?? ''),
    command: String(metadata.command ?? ''),
    target: typeof raw.target === 'string' ? raw.target : undefined,
    diffs,
    impact: asImpact(metadata.impact),
    createdAt: String(raw.requested_at ?? new Date().toISOString()),
    reviewedAt: typeof decidedAt === 'string' ? decidedAt : undefined,
    reviewedBy:
      typeof raw.decided_by === 'string'
        ? raw.decided_by
        : typeof raw.revoked_by === 'string'
          ? raw.revoked_by
          : undefined,
    feedback: typeof raw.feedback === 'string' ? raw.feedback : undefined,
    runId: typeof raw.run_id === 'string' ? raw.run_id : undefined,
    action: raw.action === 'read' || raw.action === 'propose' || raw.action === 'apply' ? raw.action : undefined,
    tool: typeof raw.tool === 'string' ? raw.tool : undefined,
    resourceScope: typeof raw.resource_scope === 'string' ? raw.resource_scope : undefined,
    expectedEffect: typeof raw.expected_effect === 'string' ? raw.expected_effect : undefined,
    executedAt: typeof raw.executed_at === 'string' ? raw.executed_at : undefined,
  }
}

export async function fetchApprovals(status?: HITLRequestStatus): Promise<HITLRequest[]> {
  const { data } = await client.get<APIResponse<Wire[]>>('/agent-approvals', {
    params: status ? { status } : undefined,
  })
  return (data.data ?? []).map(normalizeApproval)
}

async function decision(
  id: string,
  action: 'approve' | 'reject' | 'revoke',
  feedback?: string,
): Promise<HITLRequest> {
  const { data } = await client.post<APIResponse<Wire>>(
    `/agent-approvals/${encodeURIComponent(id)}/${action}`,
    feedback ? { feedback } : {},
  )
  if (!data.data) {
    throw new Error('The server did not return the persisted approval')
  }
  return normalizeApproval(data.data)
}

export function approveApproval(id: string, feedback?: string): Promise<HITLRequest> {
  return decision(id, 'approve', feedback)
}

export function rejectApproval(id: string, feedback?: string): Promise<HITLRequest> {
  return decision(id, 'reject', feedback)
}

export function revokeApproval(id: string, feedback?: string): Promise<HITLRequest> {
  return decision(id, 'revoke', feedback)
}
