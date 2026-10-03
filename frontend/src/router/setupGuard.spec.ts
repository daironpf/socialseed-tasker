import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { applySetupGuard } from '@/router/setupGuard'
import { useUiStore } from '@/stores/uiStore'
import { useToast } from '@/composables/useToast'
import * as setupApi from '@/api/setupApi'
import { setApiMode } from '@/api/client'

vi.mock('@/api/setupApi', () => ({
  getSetupStatus: vi.fn(),
}))

describe('applySetupGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    useToast().clearAll()
    setApiMode('real')
  })

  afterEach(() => {
    setApiMode('mock')
  })

  it('forces a fresh system into /setup from any main route', async () => {
    vi.mocked(setupApi.getSetupStatus).mockResolvedValue({ installed: false, needSetup: true })

    expect(await applySetupGuard({ path: '/' })).toEqual({ path: '/setup', replace: true })
    expect(await applySetupGuard({ path: '/board' })).toEqual({ path: '/setup', replace: true })
    expect(await applySetupGuard({ path: '/graph' })).toEqual({ path: '/setup', replace: true })
    expect(await applySetupGuard({ path: '/setup' })).toBe(true)
  })

  it('redirects /setup to /board when the system is already installed', async () => {
    vi.mocked(setupApi.getSetupStatus).mockResolvedValue({ installed: true, needSetup: false })

    expect(await applySetupGuard({ path: '/setup' })).toEqual({ path: '/board', replace: true })
    expect(await applySetupGuard({ path: '/board' })).toBe(true)
  })

  it('caches the status call so navigations do not repeat the HTTP request', async () => {
    vi.mocked(setupApi.getSetupStatus).mockResolvedValue({ installed: true, needSetup: false })
    const store = useUiStore()

    expect(await applySetupGuard({ path: '/board' })).toBe(true)
    expect(await applySetupGuard({ path: '/list' })).toBe(true)
    expect(await applySetupGuard({ path: '/graph' })).toBe(true)

    expect(setupApi.getSetupStatus).toHaveBeenCalledTimes(1)
    expect(store.setupChecked).toBe(true)
    expect(store.isInstalled).toBe(true)
  })

  it('keeps the mock demo intact without calling the setup API', async () => {
    setApiMode('mock')
    const store = useUiStore()

    expect(await applySetupGuard({ path: '/board' })).toBe(true)
    expect(await applySetupGuard({ path: '/setup' })).toBe(true)

    expect(setupApi.getSetupStatus).not.toHaveBeenCalled()
    expect(store.setupChecked).toBe(false)
    expect(store.isInstalled).toBeNull()
  })

  it('does not block navigation when the status check fails and warns only once', async () => {
    vi.mocked(setupApi.getSetupStatus).mockRejectedValue(new Error('network down'))
    const store = useUiStore()

    expect(await applySetupGuard({ path: '/board' })).toBe(true)
    expect(await applySetupGuard({ path: '/list' })).toBe(true)

    expect(store.isInstalled).toBeNull()
    expect(store.setupChecked).toBe(true)
    expect(setupApi.getSetupStatus).toHaveBeenCalledTimes(1)
    const warnings = useToast().toasts.value.filter((toast) => toast.type === 'warning')
    expect(warnings).toHaveLength(1)
    expect(warnings[0].message).toBeTruthy()
  })
})
