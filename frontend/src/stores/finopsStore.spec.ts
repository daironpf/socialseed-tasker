import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useFinopsStore } from '@/stores/finopsStore'
import { setApiMode } from '@/api/client'

describe('finopsStore', () => {
  beforeEach(() => {
    setApiMode('mock')
    setActivePinia(createPinia())
  })

  afterEach(() => {
    setApiMode('mock')
  })

  it('loads mock fixtures in mock mode', () => {
    const store = useFinopsStore()
    expect(store.models.length).toBeGreaterThan(0)
    expect(store.caps.length).toBeGreaterThan(0)
    expect(store.metrics.totalCost).toBeGreaterThan(0)
  })

  it('starts empty in real mode', () => {
    setApiMode('real')
    setActivePinia(createPinia())
    const store = useFinopsStore()
    expect(store.models).toEqual([])
    expect(store.components).toEqual([])
    expect(store.tasks).toEqual([])
    expect(store.alerts).toEqual([])
    expect(store.caps).toEqual([])
    expect(store.metrics.totalCost).toBe(0)
    expect(store.criticalAlerts).toEqual([])
  })

  it('clears fixtures when apiMode switches to real', async () => {
    const store = useFinopsStore()
    expect(store.models.length).toBeGreaterThan(0)

    setApiMode('real')
    await nextTick()
    expect(store.models).toEqual([])
    expect(store.roi).toEqual([])
  })
})
