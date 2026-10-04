import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useHitlStore } from '@/stores/hitlStore'
import { setApiMode } from '@/api/client'
import type { HITLRequest } from '@/types/hitl'

function fakeRequest(): HITLRequest {
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
  }
}

describe('hitlStore', () => {
  beforeEach(() => {
    setApiMode('mock')
    setActivePinia(createPinia())
  })

  afterEach(() => {
    setApiMode('mock')
  })

  it('never loads demo requests in real mode', async () => {
    setApiMode('real')
    setActivePinia(createPinia())
    const store = useHitlStore()

    await store.fetchRequests()

    expect(store.requests).toEqual([])
    expect(store.pendingCount).toBe(0)
    expect(store.urgentPendingCount).toBe(0)
  })

  it('clears requests when apiMode switches to real', async () => {
    const store = useHitlStore()
    store.requests.push(fakeRequest())
    expect(store.pendingCount).toBe(1)

    setApiMode('real')
    await nextTick()

    expect(store.requests).toEqual([])
    expect(store.pendingCount).toBe(0)
  })
})
