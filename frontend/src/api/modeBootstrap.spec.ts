import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { resolveInitialApiMode, resetApiModeProbe } from '@/api/modeBootstrap'
import { apiMode, API_MODE_STORAGE_KEY, setApiMode } from '@/api/client'

const fetchMock = vi.fn()

describe('modeBootstrap', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('fetch', fetchMock)
    localStorage.clear()
    // Fresh browser simulation: mock default with no stored choice.
    apiMode.value = 'mock'
    resetApiModeProbe()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it('switches to real mode when the backend answers the probe', async () => {
    fetchMock.mockResolvedValue({ ok: true })

    await resolveInitialApiMode()

    expect(fetchMock).toHaveBeenCalledWith('/api/v1/health', expect.anything())
    expect(apiMode.value).toBe('real')
    expect(localStorage.getItem(API_MODE_STORAGE_KEY)).toBe('real')
  })

  it('keeps the mock default (unpersisted) when the backend is unreachable', async () => {
    fetchMock.mockRejectedValue(new Error('network down'))

    await resolveInitialApiMode()

    expect(apiMode.value).toBe('mock')
    expect(localStorage.getItem(API_MODE_STORAGE_KEY)).toBeNull()
  })

  it('keeps the mock default when the probe answers not ok', async () => {
    fetchMock.mockResolvedValue({ ok: false })

    await resolveInitialApiMode()

    expect(apiMode.value).toBe('mock')
    expect(localStorage.getItem(API_MODE_STORAGE_KEY)).toBeNull()
  })

  it('respects an explicit stored mode without probing', async () => {
    localStorage.setItem(API_MODE_STORAGE_KEY, 'mock')

    await resolveInitialApiMode()

    expect(fetchMock).not.toHaveBeenCalled()
    expect(apiMode.value).toBe('mock')
  })

  it('does not probe when the mode is already real', async () => {
    setApiMode('real')
    localStorage.removeItem(API_MODE_STORAGE_KEY)

    await resolveInitialApiMode()

    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('probes only once per page load', async () => {
    fetchMock.mockResolvedValue({ ok: true })

    await resolveInitialApiMode()
    await resolveInitialApiMode()

    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
