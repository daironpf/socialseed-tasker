import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMcpStore } from '@/stores/mcpStore'
import * as mcpApi from '@/api/mcpApi'
import { connectSSE, type SSEHandle } from '@/api/realtime'
import { setApiMode } from '@/api/client'
import type { MCPSession, MCPServer, MCPToolCall } from '@/types/mcp'

vi.mock('@/api/mcpApi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/mcpApi')>()
  return {
    ...actual,
    fetchSessions: vi.fn(),
    fetchServers: vi.fn(),
    fetchToolCalls: vi.fn(),
    saveSession: vi.fn(),
    rerunToolCall: vi.fn(),
  }
})

vi.mock('@/api/realtime', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/realtime')>()
  return {
    ...actual,
    connectSSE: vi.fn(() => ({ close: vi.fn() })),
  }
})

function makeSession(overrides: Partial<MCPSession> = {}): MCPSession {
  return {
    id: 's1',
    clientName: 'Cursor IDE',
    clientType: 'cursor',
    status: 'active',
    connectedAt: '2026-09-29T00:00:00Z',
    lastActivityAt: '2026-09-29T01:00:00Z',
    uptime: 3600,
    contextConsumed: 1024,
    contextLimit: 524288,
    cypherQueries: 10,
    cypherQueriesPerMin: 1,
    toolsUsed: ['read_file'],
    projectId: 'p1',
    userId: 'u1',
    server: null,
    ...overrides,
  }
}

function makeServer(overrides: Partial<MCPServer> = {}): MCPServer {
  return {
    id: 'srv1',
    name: 'neo4j-mcp',
    transport: 'http',
    url: 'http://localhost:8080/mcp',
    tools: ['rag_search'],
    status: 'online',
    lastSeen: '2026-09-29T01:00:00Z',
    ...overrides,
  }
}

function makeCall(overrides: Partial<MCPToolCall> = {}): MCPToolCall {
  return {
    id: 'c1',
    sessionId: 's1',
    server: 'neo4j-mcp',
    tool: 'rag_search',
    arguments: { query: 'auth bug' },
    status: 'success',
    startedAt: '2026-09-29T01:00:00Z',
    durationMs: 100,
    resultSummary: '2 chunk(s) matched',
    error: null,
    rerunOf: null,
    ...overrides,
  }
}

describe('mcpStore', () => {
  let store: ReturnType<typeof useMcpStore>

  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    setApiMode('real')
    store = useMcpStore()
  })

  afterEach(() => {
    store.stopStream()
    setApiMode('mock')
  })

  it('loads sessions, servers and tool calls from the real API', async () => {
    vi.mocked(mcpApi.fetchSessions).mockResolvedValue([makeSession()])
    vi.mocked(mcpApi.fetchServers).mockResolvedValue([makeServer()])
    vi.mocked(mcpApi.fetchToolCalls).mockResolvedValue([makeCall()])

    await store.fetchSessions()

    expect(store.sessions).toHaveLength(1)
    expect(store.sessions[0].clientName).toBe('Cursor IDE')
    expect(store.servers[0].name).toBe('neo4j-mcp')
    expect(store.toolCalls[0].tool).toBe('rag_search')
    expect(store.source).toBe('live')
    expect(store.error).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('captures API failures as a store error', async () => {
    vi.mocked(mcpApi.fetchSessions).mockRejectedValue(new Error('boom'))

    await store.fetchSessions()

    expect(store.error).toBe('boom')
    expect(store.sessions).toHaveLength(0)
    expect(store.loading).toBe(false)
  })

  it('computes latency metrics with slow detection', async () => {
    vi.mocked(mcpApi.fetchSessions).mockResolvedValue([])
    vi.mocked(mcpApi.fetchServers).mockResolvedValue([])
    vi.mocked(mcpApi.fetchToolCalls).mockResolvedValue([
      makeCall({ id: 'c1', tool: 'rag_search', durationMs: 100, status: 'success' }),
      makeCall({ id: 'c2', tool: 'rag_search', durationMs: 300, status: 'success' }),
      makeCall({ id: 'c3', tool: 'execute_cypher', durationMs: 2000, status: 'error', error: 'fail' }),
      makeCall({ id: 'c4', tool: 'execute_cypher', durationMs: null, status: 'running' }),
    ])

    await store.fetchSessions()

    expect(store.toolMetrics).toEqual([
      { tool: 'rag_search', calls: 2, successes: 2, errors: 0, avgMs: 200, maxMs: 300, slow: false },
      { tool: 'execute_cypher', calls: 2, successes: 0, errors: 1, avgMs: 2000, maxMs: 2000, slow: true },
    ])
  })

  it('wires the SSE stream and applies live events', async () => {
    store.startStream()

    expect(connectSSE).toHaveBeenCalledTimes(1)
    const [path, handlers, options] = vi.mocked(connectSSE).mock.calls[0]
    expect(path).toBe('/mcp/tool-calls/stream')
    expect(options?.events).toContain('tool_calls')

    handlers.onState?.('live')
    expect(store.streamConnected).toBe(true)
    handlers.onState?.('offline')
    expect(store.streamConnected).toBe(false)

    handlers.onEvent('tool_calls', { calls: [makeCall({ id: 'c10' })] })
    expect(store.toolCalls.map(c => c.id)).toEqual(['c10'])

    handlers.onEvent('tool_call', { ...makeCall({ id: 'c11', tool: 'new_tool' }) })
    expect(store.toolCalls[0].id).toBe('c11')
    expect(store.toolCalls[0].tool).toBe('new_tool')

    handlers.onEvent('session_update', { ...makeSession({ id: 's9', clientName: 'Windsurf' }) })
    expect(store.sessions.find(s => s.id === 's9')?.clientName).toBe('Windsurf')

    handlers.onEvent('session_removed', { id: 's9' })
    expect(store.sessions.find(s => s.id === 's9')).toBeUndefined()

    const handle = vi.mocked(connectSSE).mock.results[0].value as SSEHandle
    store.stopStream()
    expect(handle.close).toHaveBeenCalled()
    expect(store.streamConnected).toBe(false)
  })

  it('re-runs a tool call through the API and tracks the new record', async () => {
    vi.mocked(mcpApi.fetchSessions).mockResolvedValue([])
    vi.mocked(mcpApi.fetchServers).mockResolvedValue([])
    vi.mocked(mcpApi.fetchToolCalls).mockResolvedValue([makeCall({ id: 'c1' })])
    await store.fetchSessions()
    vi.mocked(mcpApi.rerunToolCall).mockResolvedValue(
      makeCall({ id: 'r1', rerunOf: 'c1', durationMs: 42, resultSummary: 're-run ok' }),
    )

    const rerun = await store.rerunToolCall('c1')

    expect(mcpApi.rerunToolCall).toHaveBeenCalledWith('c1')
    expect(rerun?.rerunOf).toBe('c1')
    expect(store.toolCalls.find(c => c.id === 'r1')?.resultSummary).toBe('re-run ok')
    expect(store.error).toBeNull()
  })

  it('pauses an active session through the API', async () => {
    vi.mocked(mcpApi.fetchSessions).mockResolvedValue([makeSession()])
    vi.mocked(mcpApi.fetchServers).mockResolvedValue([])
    vi.mocked(mcpApi.fetchToolCalls).mockResolvedValue([])
    await store.fetchSessions()
    vi.mocked(mcpApi.saveSession).mockResolvedValue(makeSession({ status: 'paused' }))

    const ok = await store.pauseSession('s1')

    expect(ok).toBe(true)
    expect(mcpApi.saveSession).toHaveBeenCalledWith({
      id: 's1',
      clientName: 'Cursor IDE',
      status: 'paused',
    })
    expect(store.sessions[0].status).toBe('paused')
  })

  it('refuses to pause a non-active session', async () => {
    vi.mocked(mcpApi.fetchSessions).mockResolvedValue([makeSession({ status: 'paused' })])
    vi.mocked(mcpApi.fetchServers).mockResolvedValue([])
    vi.mocked(mcpApi.fetchToolCalls).mockResolvedValue([])
    await store.fetchSessions()

    const ok = await store.pauseSession('s1')

    expect(ok).toBe(false)
    expect(mcpApi.saveSession).not.toHaveBeenCalled()
  })

  it('uses mock fixtures and a local ticker in mock mode', async () => {
    setApiMode('mock')

    await store.fetchSessions()

    expect(mcpApi.fetchSessions).not.toHaveBeenCalled()
    expect(store.source).toBe('mock')
    expect(store.sessions).toHaveLength(6)
    expect(store.servers).toHaveLength(2)
    expect(store.toolCalls).toHaveLength(8)

    store.startStream()
    expect(store.streamConnected).toBe(true)
    store.stopStream()
    expect(store.streamConnected).toBe(false)
  })

  it('simulates a re-run from mock fixtures', async () => {
    setApiMode('mock')
    await store.fetchSessions()

    const rerun = await store.rerunToolCall('call-m04')

    expect(rerun?.rerunOf).toBe('call-m04')
    expect(rerun?.status).toBe('success')
    expect(rerun?.resultSummary).toContain('Simulated re-run of rag_search')
    expect(store.toolCalls.find(c => c.rerunOf === 'call-m04')).toBeTruthy()
  })
})
