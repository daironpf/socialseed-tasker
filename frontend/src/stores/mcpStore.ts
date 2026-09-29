import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  MCPServer,
  MCPSession,
  MCPSessionStatus,
  MCPMetrics,
  MCPToolCall,
  MCPToolMetric,
} from '@/types/mcp'
import { isMockMode } from '@/api/client'
import * as mcpApi from '@/api/mcpApi'
import { connectSSE, type SSEHandle } from '@/api/realtime'

const MOCK_SESSIONS: MCPSession[] = [
  {
    id: 'mcp-sess-001',
    clientName: 'Cursor IDE',
    clientType: 'cursor',
    status: 'active',
    connectedAt: new Date(Date.now() - 3600000 * 2).toISOString(),
    lastActivityAt: new Date(Date.now() - 30000).toISOString(),
    uptime: 7200,
    contextConsumed: 145600,
    contextLimit: 524288,
    cypherQueries: 847,
    cypherQueriesPerMin: 12.4,
    toolsUsed: ['read_file', 'search_graph', 'execute_cypher', 'impact_analysis'],
    projectId: 'proj-001',
    userId: 'user-alice',
  },
  {
    id: 'mcp-sess-002',
    clientName: 'Claude Desktop',
    clientType: 'claude-desktop',
    status: 'active',
    connectedAt: new Date(Date.now() - 3600000 * 5).toISOString(),
    lastActivityAt: new Date(Date.now() - 120000).toISOString(),
    uptime: 18000,
    contextConsumed: 312400,
    contextLimit: 524288,
    cypherQueries: 2341,
    cypherQueriesPerMin: 8.7,
    toolsUsed: ['read_file', 'search_graph', 'execute_cypher', 'create_issue', 'update_issue'],
    projectId: 'proj-001',
    userId: 'user-bob',
  },
  {
    id: 'mcp-sess-003',
    clientName: 'Windsurf',
    clientType: 'windsurf',
    status: 'paused',
    connectedAt: new Date(Date.now() - 3600000 * 1).toISOString(),
    lastActivityAt: new Date(Date.now() - 600000).toISOString(),
    uptime: 3600,
    contextConsumed: 67200,
    contextLimit: 524288,
    cypherQueries: 234,
    cypherQueriesPerMin: 0,
    toolsUsed: ['read_file', 'search_graph'],
    projectId: 'proj-002',
    userId: 'user-alice',
  },
  {
    id: 'mcp-sess-004',
    clientName: 'VS Code Extension',
    clientType: 'vscode',
    status: 'active',
    connectedAt: new Date(Date.now() - 3600000 * 0.5).toISOString(),
    lastActivityAt: new Date(Date.now() - 10000).toISOString(),
    uptime: 1800,
    contextConsumed: 23400,
    contextLimit: 524288,
    cypherQueries: 89,
    cypherQueriesPerMin: 15.2,
    toolsUsed: ['read_file', 'search_graph', 'execute_cypher'],
    projectId: 'proj-001',
    userId: 'user-carol',
  },
  {
    id: 'mcp-sess-005',
    clientName: 'Custom Agent',
    clientType: 'custom',
    status: 'idle',
    connectedAt: new Date(Date.now() - 3600000 * 8).toISOString(),
    lastActivityAt: new Date(Date.now() - 3600000).toISOString(),
    uptime: 28800,
    contextConsumed: 498000,
    contextLimit: 524288,
    cypherQueries: 5672,
    cypherQueriesPerMin: 0.1,
    toolsUsed: ['read_file', 'search_graph', 'execute_cypher', 'create_issue', 'update_issue', 'impact_analysis'],
    projectId: 'proj-003',
    userId: 'user-dave',
  },
  {
    id: 'mcp-sess-006',
    clientName: 'Cursor IDE',
    clientType: 'cursor',
    status: 'revoked',
    connectedAt: new Date(Date.now() - 3600000 * 12).toISOString(),
    lastActivityAt: new Date(Date.now() - 3600000 * 3).toISOString(),
    uptime: 32400,
    contextConsumed: 512000,
    contextLimit: 524288,
    cypherQueries: 8934,
    cypherQueriesPerMin: 0,
    toolsUsed: ['read_file', 'search_graph', 'execute_cypher', 'create_issue'],
    projectId: 'proj-002',
    userId: 'user-eve',
  },
]

const MOCK_SERVERS: MCPServer[] = [
  {
    id: 'srv-neo4j',
    name: 'neo4j-mcp',
    transport: 'http',
    url: 'http://localhost:8080/mcp',
    tools: ['execute_cypher', 'search_graph', 'rag_search', 'rag_stats'],
    status: 'online',
    lastSeen: new Date(Date.now() - 60000).toISOString(),
  },
  {
    id: 'srv-tasker',
    name: 'tasker-mcp',
    transport: 'stdio',
    url: null,
    tools: ['impact_analysis', 'read_file', 'create_issue'],
    status: 'online',
    lastSeen: new Date(Date.now() - 180000).toISOString(),
  },
]

const MOCK_TOOL_CALLS: MCPToolCall[] = [
  {
    id: 'call-m01', sessionId: 'mcp-sess-001', server: 'neo4j-mcp', tool: 'execute_cypher',
    arguments: { query: 'MATCH (i:Issue) WHERE i.status = "OPEN" RETURN i LIMIT 10', apiKey: '[REDACTED]' },
    status: 'success', startedAt: new Date(Date.now() - 600000).toISOString(), durationMs: 1240,
    resultSummary: '10 rows returned', error: null, rerunOf: null,
  },
  {
    id: 'call-m02', sessionId: 'mcp-sess-002', server: 'neo4j-mcp', tool: 'search_graph',
    arguments: { query: 'auth module classes' },
    status: 'success', startedAt: new Date(Date.now() - 540000).toISOString(), durationMs: 320,
    resultSummary: '18 nodes matched', error: null, rerunOf: null,
  },
  {
    id: 'call-m03', sessionId: 'mcp-sess-001', server: 'neo4j-mcp', tool: 'search_graph',
    arguments: { query: 'rate limiting middleware' },
    status: 'success', startedAt: new Date(Date.now() - 480000).toISOString(), durationMs: 280,
    resultSummary: '6 nodes matched', error: null, rerunOf: null,
  },
  {
    id: 'call-m04', sessionId: 'mcp-sess-004', server: 'neo4j-mcp', tool: 'rag_search',
    arguments: { query: 'circular dependency in auth module', limit: 5, threshold: 0.7 },
    status: 'success', startedAt: new Date(Date.now() - 420000).toISOString(), durationMs: 95,
    resultSummary: '2 chunk(s) matched', error: null, rerunOf: null,
  },
  {
    id: 'call-m05', sessionId: 'mcp-sess-004', server: 'neo4j-mcp', tool: 'rag_search',
    arguments: { query: 'websocket reconnect loop', limit: 5, threshold: 0.7 },
    status: 'error', startedAt: new Date(Date.now() - 360000).toISOString(), durationMs: 410,
    resultSummary: null, error: 'Neo4j not connected', rerunOf: null,
  },
  {
    id: 'call-m06', sessionId: 'mcp-sess-002', server: 'tasker-mcp', tool: 'impact_analysis',
    arguments: { issueId: 'ISS-042' },
    status: 'success', startedAt: new Date(Date.now() - 300000).toISOString(), durationMs: 860,
    resultSummary: 'Analyzes 14 issues, 3 components', error: null, rerunOf: null,
  },
  {
    id: 'call-m07', sessionId: 'mcp-sess-003', server: 'tasker-mcp', tool: 'read_file',
    arguments: { path: 'src/auth/token.ts' },
    status: 'success', startedAt: new Date(Date.now() - 240000).toISOString(), durationMs: 45,
    resultSummary: '218 lines read', error: null, rerunOf: null,
  },
  {
    id: 'call-m08', sessionId: 'mcp-sess-001', server: 'neo4j-mcp', tool: 'execute_cypher',
    arguments: { query: 'MATCH (c:Component) RETURN c.name' },
    status: 'running', startedAt: new Date(Date.now() - 5000).toISOString(), durationMs: null,
    resultSummary: null, error: null, rerunOf: null,
  },
]

const TOOL_CALL_LIMIT = 200
const SLOW_TOOL_THRESHOLD_MS = 800

export const useMcpStore = defineStore('mcp', () => {
  const sessions = ref<MCPSession[]>([])
  const servers = ref<MCPServer[]>([])
  const toolCalls = ref<MCPToolCall[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const streamConnected = ref(false)

  const source = computed<'mock' | 'live'>(() => (isMockMode() ? 'mock' : 'live'))

  const activeSessions = computed(() => sessions.value.filter(s => s.status === 'active'))
  const pausedSessions = computed(() => sessions.value.filter(s => s.status === 'paused'))
  const revokedSessions = computed(() => sessions.value.filter(s => s.status === 'revoked'))
  const idleSessions = computed(() => sessions.value.filter(s => s.status === 'idle'))

  const metrics = computed<MCPMetrics>(() => {
    const all = sessions.value
    const active = activeSessions.value
    return {
      totalSessions: all.length,
      activeSessions: active.length,
      totalContextConsumed: all.reduce((sum, s) => sum + s.contextConsumed, 0),
      totalCypherQueries: all.reduce((sum, s) => sum + s.cypherQueries, 0),
      avgQueriesPerMin: active.length > 0
        ? active.reduce((sum, s) => sum + s.cypherQueriesPerMin, 0) / active.length
        : 0,
      avgContextPerSession: all.length > 0
        ? all.reduce((sum, s) => sum + s.contextConsumed, 0) / all.length
        : 0,
    }
  })

  const toolMetrics = computed<MCPToolMetric[]>(() => {
    const byTool = new Map<string, { calls: number; successes: number; errors: number; totalMs: number; timed: number; maxMs: number }>()
    for (const call of toolCalls.value) {
      const entry = byTool.get(call.tool) ?? { calls: 0, successes: 0, errors: 0, totalMs: 0, timed: 0, maxMs: 0 }
      entry.calls++
      if (call.status === 'success') entry.successes++
      if (call.status === 'error') entry.errors++
      if (call.status !== 'running' && typeof call.durationMs === 'number') {
        entry.totalMs += call.durationMs
        entry.timed++
        entry.maxMs = Math.max(entry.maxMs, call.durationMs)
      }
      byTool.set(call.tool, entry)
    }
    return [...byTool.entries()]
      .map(([tool, entry]) => {
        const avgMs = entry.timed > 0 ? Math.round(entry.totalMs / entry.timed) : 0
        return {
          tool,
          calls: entry.calls,
          successes: entry.successes,
          errors: entry.errors,
          avgMs,
          maxMs: entry.maxMs,
          slow: avgMs > SLOW_TOOL_THRESHOLD_MS,
        }
      })
      .sort((a, b) => b.calls - a.calls)
  })

  function errorMessage(e: unknown): string {
    return e instanceof Error ? e.message : String(e)
  }

  function upsertSession(session: MCPSession) {
    const idx = sessions.value.findIndex(s => s.id === session.id)
    if (idx >= 0) sessions.value[idx] = session
    else sessions.value = [...sessions.value, session]
  }

  function upsertServer(server: MCPServer) {
    const idx = servers.value.findIndex(s => s.id === server.id)
    if (idx >= 0) servers.value[idx] = server
    else servers.value = [...servers.value, server]
  }

  function upsertCall(call: MCPToolCall) {
    const idx = toolCalls.value.findIndex(c => c.id === call.id)
    if (idx >= 0) toolCalls.value[idx] = call
    else toolCalls.value = [call, ...toolCalls.value].slice(0, TOOL_CALL_LIMIT)
  }

  async function fetchSessions() {
    loading.value = true
    error.value = null
    try {
      if (isMockMode()) {
        await new Promise(resolve => setTimeout(resolve, 300))
        sessions.value = [...MOCK_SESSIONS]
        servers.value = [...MOCK_SERVERS]
        toolCalls.value = [...MOCK_TOOL_CALLS]
        return
      }
      const [sessionList, serverList, callList] = await Promise.all([
        mcpApi.fetchSessions(),
        mcpApi.fetchServers(),
        mcpApi.fetchToolCalls(),
      ])
      sessions.value = sessionList
      servers.value = serverList
      toolCalls.value = callList
    } catch (e) {
      error.value = errorMessage(e)
    } finally {
      loading.value = false
    }
  }

  async function updateSessionStatus(id: string, status: MCPSessionStatus): Promise<boolean> {
    const session = sessions.value.find(s => s.id === id)
    if (!session) return false
    if (isMockMode()) {
      session.status = status
      session.lastActivityAt = new Date().toISOString()
      if (status === 'paused') session.cypherQueriesPerMin = 0
      if (status === 'active') session.cypherQueriesPerMin = Math.random() * 15 + 1
      return true
    }
    try {
      const updated = await mcpApi.saveSession({ id, clientName: session.clientName, status })
      upsertSession(updated)
      error.value = null
      return true
    } catch (e) {
      error.value = errorMessage(e)
      return false
    }
  }

  async function revokeSession(id: string): Promise<boolean> {
    return updateSessionStatus(id, 'revoked')
  }

  async function pauseSession(id: string): Promise<boolean> {
    const session = sessions.value.find(s => s.id === id)
    if (!session || session.status !== 'active') return false
    return updateSessionStatus(id, 'paused')
  }

  async function resumeSession(id: string): Promise<boolean> {
    const session = sessions.value.find(s => s.id === id)
    if (!session || session.status !== 'paused') return false
    return updateSessionStatus(id, 'active')
  }

  function handleStreamEvent(event: string, data: unknown) {
    const payload = (data ?? {}) as Record<string, unknown>
    if (event === 'tool_calls') {
      const calls = Array.isArray(payload.calls) ? payload.calls : []
      toolCalls.value = calls.map(c => mcpApi.normalizeToolCall(c as Record<string, unknown>))
      return
    }
    if (event === 'tool_call' || event === 'tool_call_update') {
      upsertCall(mcpApi.normalizeToolCall(payload))
      return
    }
    if (event === 'server_update') {
      upsertServer(mcpApi.normalizeServer(payload))
      return
    }
    if (event === 'session_update') {
      upsertSession(mcpApi.normalizeSession(payload))
      return
    }
    if (event === 'session_removed') {
      const id = String(payload.id ?? '')
      sessions.value = sessions.value.filter(s => s.id !== id)
    }
  }

  let sseHandle: SSEHandle | null = null
  let mockTimer: ReturnType<typeof setInterval> | null = null

  function startStream() {
    if (isMockMode()) {
      if (mockTimer) return
      streamConnected.value = true
      mockTimer = setInterval(() => {
        if (!streamConnected.value || !isMockMode()) {
          if (mockTimer) {
            clearInterval(mockTimer)
            mockTimer = null
          }
          return
        }
        sessions.value.forEach(session => {
          if (session.status === 'active') {
            session.cypherQueries += Math.floor(Math.random() * 3)
            session.cypherQueriesPerMin = Math.round((Math.random() * 15 + 1) * 10) / 10
            session.contextConsumed = Math.min(
              session.contextLimit,
              session.contextConsumed + Math.floor(Math.random() * 2048)
            )
            session.lastActivityAt = new Date().toISOString()
            session.uptime += 5
          }
        })
      }, 5000)
      return
    }
    if (sseHandle) return
    sseHandle = connectSSE(
      '/mcp/tool-calls/stream',
      {
        onEvent: (event, data) => handleStreamEvent(event, data),
        onState: (state) => {
          streamConnected.value = state === 'live'
        },
      },
      {
        events: [
          'connected',
          'tool_calls',
          'tool_call',
          'tool_call_update',
          'server_update',
          'session_update',
          'session_removed',
          'ping',
        ],
      },
    )
  }

  function stopStream() {
    if (mockTimer) {
      clearInterval(mockTimer)
      mockTimer = null
    }
    if (sseHandle) {
      sseHandle.close()
      sseHandle = null
    }
    streamConnected.value = false
  }

  async function rerunToolCall(callId: string): Promise<MCPToolCall | null> {
    const original = toolCalls.value.find(c => c.id === callId)
    if (!original) return null
    if (isMockMode()) {
      const rerun: MCPToolCall = {
        ...original,
        id: `call-${Date.now()}`,
        status: 'success',
        startedAt: new Date().toISOString(),
        durationMs: Math.floor(Math.random() * 200) + 30,
        resultSummary: `Simulated re-run of ${original.tool}`,
        error: null,
        rerunOf: callId,
      }
      upsertCall(rerun)
      return rerun
    }
    try {
      const rerun = await mcpApi.rerunToolCall(callId)
      upsertCall(rerun)
      error.value = null
      return rerun
    } catch (e) {
      error.value = errorMessage(e)
      return null
    }
  }

  function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1048576).toFixed(2)} MB`
  }

  function formatUptime(seconds: number): string {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    if (hrs > 0) return `${hrs}h ${mins}m`
    return `${mins}m`
  }

  function getClientIcon(type: string): string {
    const icons: Record<string, string> = {
      cursor: '⚡',
      'claude-desktop': '🤖',
      windsurf: '🏄',
      vscode: '💻',
      custom: '🔧',
    }
    return icons[type] || '🔌'
  }

  function getStatusColor(status: MCPSessionStatus): string {
    const colors: Record<MCPSessionStatus, string> = {
      active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      paused: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      revoked: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      idle: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
    }
    return colors[status]
  }

  function getCallStatusColor(status: MCPToolCall['status']): string {
    const colors: Record<MCPToolCall['status'], string> = {
      running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      success: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    }
    return colors[status]
  }

  return {
    sessions,
    servers,
    toolCalls,
    loading,
    error,
    streamConnected,
    source,
    activeSessions,
    pausedSessions,
    revokedSessions,
    idleSessions,
    metrics,
    toolMetrics,
    fetchSessions,
    revokeSession,
    pauseSession,
    resumeSession,
    rerunToolCall,
    startStream,
    stopStream,
    formatBytes,
    formatUptime,
    getClientIcon,
    getStatusColor,
    getCallStatusColor,
  }
})
