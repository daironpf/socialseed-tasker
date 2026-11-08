import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

import client from '@/api/client'
import { approveApproval, fetchApprovals, normalizeApproval } from '@/api/hitlApi'

function wire(overrides: Record<string, unknown> = {}) {
  return {
    id: 'approval-1',
    run_id: 'run-1',
    agent_id: 'agent-1',
    issue_id: 'issue-1',
    project_id: 'project-1',
    action: 'apply',
    tool: 'neo4j_query',
    resource_scope: 'graph',
    target: 'production',
    expected_effect: 'archive nodes',
    action_payload: {},
    request_metadata: {
      title: 'Archive nodes',
      description: 'Cleanup',
      type: 'schema_migration',
      severity: 'HIGH',
      component: 'backend',
      issue_title: 'Cleanup graph',
      command: 'MATCH (n) RETURN n',
      diffs: [{ filename: 'migration.cypher', content: 'MATCH (n)' }],
      impact: {
        totalAffected: 2,
        directDeps: 1,
        transitiveDeps: 1,
        riskLevel: 'HIGH',
        affectedComponents: ['backend'],
      },
    },
    status: 'pending',
    requested_at: '2026-01-01T10:00:00+00:00',
    expires_at: null,
    decided_at: null,
    decided_by: null,
    feedback: null,
    revoked_at: null,
    revoked_by: null,
    executed_at: null,
    ...overrides,
  }
}

describe('hitlApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('maps the persisted snake_case approval to the HITL UI model', () => {
    const request = normalizeApproval(wire())

    expect(request.id).toBe('approval-1')
    expect(request.title).toBe('Archive nodes')
    expect(request.type).toBe('schema_migration')
    expect(request.severity).toBe('HIGH')
    expect(request.status).toBe('pending')
    expect(request.agentId).toBe('agent-1')
    expect(request.issueId).toBe('issue-1')
    expect(request.component).toBe('backend')
    expect(request.command).toBe('MATCH (n) RETURN n')
    expect(request.diffs).toEqual([
      { filename: 'migration.cypher', content: 'MATCH (n)' },
    ])
    expect(request.impact.totalAffected).toBe(2)
    expect(request.runId).toBe('run-1')
    expect(request.expectedEffect).toBe('archive nodes')
  })

  it('exposes revoked and expired server states', () => {
    const revoked = normalizeApproval(
      wire({
        status: 'revoked',
        revoked_at: '2026-01-01T11:00:00+00:00',
        revoked_by: 'human-admin',
        feedback: 'scope changed',
      }),
    )
    const expired = normalizeApproval(wire({ status: 'expired' }))

    expect(revoked.status).toBe('revoked')
    expect(revoked.reviewedBy).toBe('human-admin')
    expect(revoked.reviewedAt).toBe('2026-01-01T11:00:00+00:00')
    expect(revoked.feedback).toBe('scope changed')
    expect(expired.status).toBe('expired')
  })

  it('fetches approvals with an optional status filter', async () => {
    vi.mocked(client.get).mockResolvedValue({ data: { data: [wire()] } } as never)

    const rows = await fetchApprovals('pending')

    expect(client.get).toHaveBeenCalledWith('/agent-approvals', {
      params: { status: 'pending' },
    })
    expect(rows).toHaveLength(1)
  })

  it('posts human decisions and maps the persisted result', async () => {
    vi.mocked(client.post).mockResolvedValue({
      data: { data: wire({ status: 'approved', decided_by: 'human-admin' }) },
    } as never)

    const request = await approveApproval('approval-1', 'ok')

    expect(client.post).toHaveBeenCalledWith('/agent-approvals/approval-1/approve', {
      feedback: 'ok',
    })
    expect(request.status).toBe('approved')
    expect(request.reviewedBy).toBe('human-admin')
  })
})
