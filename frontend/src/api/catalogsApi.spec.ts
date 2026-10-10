import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import { fetchSkills, fetchTools, resetCatalogsCache } from '@/api/catalogsApi'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
  },
}))

const mockedGet = client.get as unknown as ReturnType<typeof vi.fn>

describe('catalogsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetCatalogsCache()
  })

  it('unwraps the skills envelope into catalog items (issue #572)', async () => {
    mockedGet.mockResolvedValue({
      data: { data: [{ id: 'python', name: 'Python' }, { id: 'vue', name: 'Vue' }] },
    })

    const skills = await fetchSkills()

    expect(mockedGet).toHaveBeenCalledWith('/skills', { suppressErrorToast: true })
    expect(skills).toEqual([
      { id: 'python', name: 'Python' },
      { id: 'vue', name: 'Vue' },
    ])
  })

  it('unwraps the tools envelope with descriptions', async () => {
    mockedGet.mockResolvedValue({
      data: {
        data: [
          { id: 'code_search', name: 'Code search', description: 'Search the codebase' },
          { id: 'shell', name: 'Shell', description: null },
        ],
      },
    })

    const tools = await fetchTools()

    expect(mockedGet).toHaveBeenCalledWith('/tools', { suppressErrorToast: true })
    expect(tools[0]).toEqual({ id: 'code_search', name: 'Code search', description: 'Search the codebase' })
    expect(tools[1].description).toBeNull()
  })

  it('falls back to an empty list on an empty envelope', async () => {
    mockedGet.mockResolvedValue({ data: {} })

    await expect(fetchSkills()).resolves.toEqual([])
    await expect(fetchTools()).resolves.toEqual([])
  })

  it('caches within the TTL so opening several modals hits the API once', async () => {
    mockedGet.mockResolvedValue({ data: { data: [{ id: 'python', name: 'Python' }] } })

    await fetchSkills()
    await fetchSkills()
    await fetchTools()
    await fetchTools()

    expect(mockedGet).toHaveBeenCalledTimes(2) // one per catalog
  })

  it('resetCatalogsCache clears the window for the specs', async () => {
    mockedGet.mockResolvedValue({ data: { data: [{ id: 'python', name: 'Python' }] } })

    await fetchSkills()
    resetCatalogsCache()
    await fetchSkills()

    expect(mockedGet).toHaveBeenCalledTimes(2)
  })

  it('propagates a 503 so pickers degrade to free text / local fallback', async () => {
    const unavailable = Object.assign(new Error('PostgreSQL not configured'), { status: 503 })
    mockedGet.mockRejectedValue(unavailable)

    await expect(fetchTools()).rejects.toMatchObject({ status: 503 })
  })

  it('does not cache a failed fetch', async () => {
    const unavailable = Object.assign(new Error('PostgreSQL not configured'), { status: 503 })
    mockedGet.mockRejectedValueOnce(unavailable)
    mockedGet.mockResolvedValue({ data: { data: [{ id: 'shell', name: 'Shell' }] } })

    await expect(fetchTools()).rejects.toMatchObject({ status: 503 })
    await expect(fetchTools()).resolves.toEqual([{ id: 'shell', name: 'Shell' }])
  })
})
