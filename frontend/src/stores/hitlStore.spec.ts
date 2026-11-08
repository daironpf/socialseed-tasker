import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useHitlStore } from '@/stores/hitlStore'
import { setApiMode } from '@/api/client'
import * as hitlApi from '@/api/hitlApi'
import type { HITLRequest } from '@/types/hitl'

vi.mock('@/api/hitlApi', () => ({
  fetchApprovals: vi.fn(),
  approveApproval: vi.fn(),
  rejectApproval: vi.fn(),
  revokeApproval: vi.fn(),
}))

function fakeRequest(overrides: Partial<HITLRequest> = {}): HITLRequest {
  return {
    id: 'hitl-1',
    title: 'Delete production table',
    description: '',
    type: 'delete_operation',
    severity: 'CRITICAL',
    status: 'pending',
    agentId: 'agent-1',
    agentName: 'Arch-Bot',
    agentAvatar: '🏗️',
    issueId: 'ISS-42',
    issueTitle: 'Purge users',
    component: 'api',
    command: 'DELETE users',
    diffs: [],
    impact: {
      totalAffected: 3,
      directDeps: 1,
      transitiveDeps: 2,
      riskLevel: 'CRITICAL',
      affectedComponents: ['api'],
    },
    createdAt: '2026-10-04T10:00:00Z',
    ...overrides,
  }
}

async function flushPromises() {
  await Promise.resolve()
  await Promise.resolve()
}

describe('hitlStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setApiMode('mock')
    setActivePinia(createPinia())
  })

  afterEach(() => {
    setApiMode('mock')
  })

  it('loads persisted approvals from the server in real mode', async () => {
    vi.mocked(hitlApi.fetchApprovals).mockResolvedValue([fakeRequest()])
    setApiMode('real')
    setActivePinia(createPinia())
    const store = useHitlStore()

    await store.fetchRequests()

    expect(hitlApi.fetchApprovals).toHaveBeenCalled()
    expect(store.requests).toHaveLength(1)
    expect(store.pendingCount).toBe(1)
  })

  it('clears requests when apiMode switches to real and reloads from the server', async () => {
    vi.mocked(hitlApi.fetchApprovals).mockResolvedValue([])
    const store = useHitlStore()
    store.requests.push(fakeRequest())
    expect(store.pendingCount).toBe(1)

    setApiMode('real')
    await nextTick()
    await flushPromises()

    expect(store.requests).toEqual([])
    expect(store.pendingCount).toBe(0)
    expect(hitlApi.fetchApprovals).toHaveBeenCalled()
  })

  it('uses the server response after approving', async () => {
    vi.mocked(hitlApi.fetchApprovals).mockResolvedValue([fakeRequest()])
    vi.mocked(hitlApi.approveApproval).mockResolvedValue(
      fakeRequest({ status: 'approved', reviewedBy: 'human-admin' }),
    )
    setApiMode('real')
    setActivePinia(createPinia())
    const store = useHitlStore()
    await store.fetchRequests()

    const ok = await store.approveRequest('hitl-1')

    expect(ok).toBe(true)
    expect(hitlApi.approveApproval).toHaveBeenCalledWith('hitl-1')
    expect(store.requests[0].status).toBe('approved')
  })

  it('maps request-changes to a rejection with feedback in real mode', async () => {
    vi.mocked(hitlApi.fetchApprovals).mockResolvedValue([fakeRequest()])
    vi.mocked(hitlApi.rejectApproval).mockResolvedValue(
      fakeRequest({ status: 'rejected', feedback: 'needs another scope' }),
    )
    setApiMode('real')
    setActivePinia(createPinia())
    const store = useHitlStore()
    await store.fetchRequests()

    const ok = await store.modifyRequest('hitl-1', 'needs another scope')

    expect(ok).toBe(true)
    expect(hitlApi.rejectApproval).toHaveBeenCalledWith('hitl-1', 'needs another scope')
    expect(store.requests[0].status).toBe('rejected')
  })

  it('revokes approved actions through the server', async () => {
    vi.mocked(hitlApi.fetchApprovals).mockResolvedValue([
      fakeRequest({ status: 'approved' }),
    ])
    vi.mocked(hitlApi.revokeApproval).mockResolvedValue(
      fakeRequest({ status: 'revoked', feedback: 'scope changed' }),
    )
    setApiMode('real')
    setActivePinia(createPinia())
    const store = useHitlStore()
    await store.fetchRequests()

    const ok = await store.revokeRequest('hitl-1', 'scope changed')

    expect(ok).toBe(true)
    expect(hitlApi.revokeApproval).toHaveBeenCalledWith('hitl-1', 'scope changed')
    expect(store.requests[0].status).toBe('revoked')
    expect(store.revokedRequests).toHaveLength(1)
  })

  it('keeps the previous list and exposes the error when the API fails', async () => {
    vi.mocked(hitlApi.fetchApprovals).mockRejectedValue(new Error('server down'))
    setApiMode('real')
    setActivePinia(createPinia())
    const store = useHitlStore()
    store.requests.push(fakeRequest())

    await store.fetchRequests()

    expect(store.error).toBe('server down')
    expect(store.requests).toHaveLength(1)
  })
})
