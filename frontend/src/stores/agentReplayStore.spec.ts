import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useAgentReplayStore } from '@/stores/agentReplayStore'
import { setApiMode } from '@/api/client'

describe('agentReplayStore', () => {
  beforeEach(() => {
    setApiMode('mock')
    setActivePinia(createPinia())
  })

  afterEach(() => {
    setApiMode('mock')
  })

  it('loads demo sessions in mock mode', () => {
    const store = useAgentReplayStore()
    expect(store.sessions.length).toBeGreaterThan(0)
    expect(store.selectedSessionId).toBe('session-001')
    expect(store.selectedSession).toBeTruthy()
  })

  it('starts empty in real mode', () => {
    setApiMode('real')
    setActivePinia(createPinia())
    const store = useAgentReplayStore()
    expect(store.sessions).toEqual([])
    expect(store.selectedSessionId).toBeNull()
    expect(store.selectedSession).toBeUndefined()
    expect(store.visibleEvents).toEqual([])
  })

  it('clears sessions when apiMode switches to real', async () => {
    const store = useAgentReplayStore()
    expect(store.sessions.length).toBeGreaterThan(0)

    setApiMode('real')
    await nextTick()
    expect(store.sessions).toEqual([])
    expect(store.selectedSessionId).toBeNull()
  })
})
