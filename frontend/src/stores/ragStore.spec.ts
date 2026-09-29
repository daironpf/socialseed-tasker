import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRagStore } from '@/stores/ragStore'
import * as ragApi from '@/api/ragApi'
import { setApiMode } from '@/api/client'

vi.mock('@/api/ragApi', () => ({
  searchRag: vi.fn(),
  getRagStats: vi.fn(),
}))

describe('ragStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    setApiMode('real')
  })

  afterEach(() => {
    vi.useRealTimers()
    setApiMode('mock')
  })

  it('queries the real backend and maps chunk results', async () => {
    vi.mocked(ragApi.searchRag).mockResolvedValue({
      results: [
        {
          id: 'chunk-1',
          content: 'Fix circular dependency via gateway\nExtended body of the solution',
          sourceType: 'issue_solution',
          sourceId: 'ISS-042',
          score: 0.91,
        },
      ],
      count: 1,
    })
    const store = useRagStore()

    const resp = await store.search('auth bug')

    expect(ragApi.searchRag).toHaveBeenCalledWith('auth bug', 10, 0.5)
    expect(resp.totalMatches).toBe(1)
    expect(resp.embeddingModel).toBe('neo4j-vector')
    expect(store.source).toBe('live')
    expect(store.error).toBeNull()
    const result = store.results[0]
    expect(result.issueId).toBe('ISS-042')
    expect(result.issueStatus).toBe('INDEXED')
    expect(result.similarity).toBe(0.91)
    expect(result.component).toBe('issue_solution')
    expect(result.issueTitle).toBe('Fix circular dependency via gateway')
    expect(result.solutionSummary).toContain('Extended body')
    expect(result.contextNodes).toHaveLength(2)
    expect(result.contextEdges).toHaveLength(1)
    expect(result.contextEdges[0].type).toBe('FROM')
  })

  it('surfaces backend errors from the real API', async () => {
    vi.mocked(ragApi.searchRag).mockResolvedValue({ error: 'Neo4j not connected' })
    const store = useRagStore()

    const resp = await store.search('q')

    expect(store.error).toBe('Neo4j not connected')
    expect(store.results).toHaveLength(0)
    expect(resp.totalMatches).toBe(0)
  })

  it('captures rejected API calls as a search error', async () => {
    vi.mocked(ragApi.searchRag).mockRejectedValue(new Error('network down'))
    const store = useRagStore()

    await store.search('q')

    expect(store.error).toBe('network down')
    expect(store.results).toHaveLength(0)
  })

  it('loads index stats into the metrics panel', async () => {
    vi.mocked(ragApi.getRagStats).mockResolvedValue({
      total: 12,
      by_type: { doc: 4, issue: 8 },
    })
    const store = useRagStore()

    await store.init()

    expect(store.stats).toEqual({ total: 12, by_type: { doc: 4, issue: 8 } })
    expect(store.metrics.totalEmbeddings).toBe(12)
    expect(store.metrics.topComponents).toEqual([
      { name: 'issue', count: 8 },
      { name: 'doc', count: 4 },
    ])
    expect(store.metrics.lastIndexedAt).toBeNull()
    expect(store.error).toBeNull()
  })

  it('keeps stats unavailable when the backend reports an error', async () => {
    vi.mocked(ragApi.getRagStats).mockResolvedValue({ error: 'stats failed' })
    const store = useRagStore()

    await store.init()

    expect(store.stats).toBeNull()
    expect(store.error).toBe('stats failed')
  })

  it('falls back to mock fixtures in mock mode without calling the API', async () => {
    setApiMode('mock')
    vi.useFakeTimers()
    const store = useRagStore()

    const pending = store.search('auth', 0.8, 10)
    await vi.advanceTimersByTimeAsync(900)
    const resp = await pending

    expect(ragApi.searchRag).not.toHaveBeenCalled()
    expect(store.source).toBe('mock')
    expect(resp.results).toHaveLength(3)
    expect(resp.results[0].similarity).toBe(0.94)
    expect(store.results).toHaveLength(3)
  })
})
