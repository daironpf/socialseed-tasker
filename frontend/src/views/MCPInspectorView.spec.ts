import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { setActivePinia, type Pinia } from 'pinia'
import { mountComponent } from '@/test/mount'
import MCPInspectorView from '@/views/MCPInspectorView.vue'
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

const activeSession: MCPSession = {
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
}

const neo4jServer: MCPServer = {
  id: 'srv1',
  name: 'neo4j-mcp',
  transport: 'http',
  url: 'http://localhost:8080/mcp',
  tools: ['rag_search', 'execute_cypher'],
  status: 'online',
  lastSeen: '2026-09-29T01:00:00Z',
}

const ragCall: MCPToolCall = {
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
}

const cypherCall: MCPToolCall = {
  ...ragCall,
  id: 'c2',
  tool: 'execute_cypher',
  arguments: { query: 'MATCH (i:Issue) RETURN i' },
  durationMs: 1240,
  resultSummary: '10 rows returned',
}

const rerunResult: MCPToolCall = {
  ...ragCall,
  id: 'r1',
  rerunOf: 'c1',
  durationMs: 55,
  resultSummary: 'Re-run completed',
}

describe('MCPInspectorView', () => {
  let pinia: Pinia

  beforeEach(() => {
    vi.clearAllMocks()
    setApiMode('real')
    vi.mocked(mcpApi.fetchSessions).mockResolvedValue([activeSession])
    vi.mocked(mcpApi.fetchServers).mockResolvedValue([neo4jServer])
    vi.mocked(mcpApi.fetchToolCalls).mockResolvedValue([ragCall, cypherCall])
  })

  afterEach(() => {
    document.body.innerHTML = ''
    setApiMode('mock')
  })

  async function mountView() {
    const mounted = mountComponent(MCPInspectorView)
    pinia = mounted.pinia
    setActivePinia(pinia)
    await flushPromises()
    await mounted.wrapper.vm.$nextTick()
    return mounted.wrapper
  }

  it('renders live servers, tool calls and latency metrics', async () => {
    const wrapper = await mountView()
    const text = wrapper.text()

    expect(text).toContain('Live')
    expect(text).not.toContain('Mock data')
    expect(text).toContain('MCP Servers')
    expect(text).toContain('neo4j-mcp')
    expect(text).toContain('Tool Calls')
    expect(text).toContain('execute_cypher')
    expect(text).toContain('1240 ms')
    expect(text).toContain('Latency by Tool')
    expect(text).toContain('Slow')
    expect(wrapper.find('[aria-label="Re-run tool"]').exists()).toBe(true)
  })

  it('wires the live SSE stream after sessions load and closes it on unmount', async () => {
    const wrapper = await mountView()

    expect(mcpApi.fetchSessions).toHaveBeenCalledTimes(1)
    expect(connectSSE).toHaveBeenCalledTimes(1)
    expect(vi.mocked(connectSSE).mock.calls[0][0]).toBe('/mcp/tool-calls/stream')
    expect(vi.mocked(connectSSE).mock.calls[0][2]?.events).toContain('tool_calls')

    const handle = vi.mocked(connectSSE).mock.results[0].value as SSEHandle
    wrapper.unmount()
    expect(handle.close).toHaveBeenCalled()
  })

  it('opens the payload modal and re-runs the tool call', async () => {
    vi.mocked(mcpApi.rerunToolCall).mockResolvedValue(rerunResult)
    const wrapper = await mountView()

    await wrapper.find('[aria-label="View payload"]').trigger('click')
    await wrapper.vm.$nextTick()

    const dialog = wrapper.find('[role="dialog"]')
    expect(dialog.exists()).toBe(true)
    expect(dialog.text()).toContain('Payload Inspection')
    expect(dialog.text()).toContain('rag_search')
    expect(dialog.text()).toContain('"query"')
    expect(dialog.text()).toContain('2 chunk(s) matched')

    const rerunButton = dialog
      .findAll('button')
      .find((b) => b.text().includes('Re-run tool'))
    expect(rerunButton).toBeTruthy()
    await rerunButton!.trigger('click')
    await flushPromises()
    await wrapper.vm.$nextTick()

    expect(mcpApi.rerunToolCall).toHaveBeenCalledWith('c1')
    expect(dialog.text()).toContain('Re-run completed')
    expect(wrapper.text()).toContain('Re-run completed')

    const closeButton = dialog
      .findAll('button')
      .find((b) => b.text().includes('Close'))
    await closeButton!.trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })
})
