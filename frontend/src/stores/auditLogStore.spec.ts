import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useAuditLogStore } from '@/stores/auditLogStore'
import { setApiMode } from '@/api/client'

describe('auditLogStore', () => {
  beforeEach(() => {
    setApiMode('mock')
    setActivePinia(createPinia())
  })

  afterEach(() => {
    setApiMode('mock')
  })

  it('generates demo entries in mock mode', () => {
    const store = useAuditLogStore()
    expect(store.entries.length).toBeGreaterThan(0)
    expect(store.chain.length).toBeGreaterThan(0)
  })

  it('stays empty in real mode', () => {
    setApiMode('real')
    setActivePinia(createPinia())
    const store = useAuditLogStore()
    expect(store.entries).toEqual([])
    expect(store.filteredEntries).toEqual([])
    expect(store.chain).toEqual([])
    expect(store.severityCounts).toEqual({ LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 })
  })

  it('clears and restores demo entries when apiMode switches', async () => {
    const store = useAuditLogStore()
    expect(store.entries.length).toBeGreaterThan(0)

    setApiMode('real')
    await nextTick()
    expect(store.entries).toEqual([])

    setApiMode('mock')
    await nextTick()
    expect(store.entries.length).toBeGreaterThan(0)
  })
})
